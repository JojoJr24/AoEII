"""
Tool Manager - Local and MCP Tool Integration

This module serves as a wrapper that integrates both local tool execution and Model Context Protocol (MCP) functionality.
It maintains backward compatibility with existing local tools while adding support for MCP servers that can provide
additional tools and resources.

Key features:
- Local tool loading and execution from Python modules
- MCP client for connecting to remote and local MCP servers
- Unified interface for executing both local and MCP tools
- Asynchronous support for MCP operations
- Configuration loading from cline_mcp_settings.json

The module exposes the same public interface as before:
- load_tools(): Load local tool modules
- generate_tool_descriptions(): Get descriptions for all tools (local + MCP)
- parse_tool_calls(): Parse tool calls from LLM responses
- execute_tools(): Execute tool calls (handles both local and MCP tools)
"""

import os
import json
import importlib.util
from utils import BLUE, MAGENTA, GREEN, debug_print
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional

class McpClient:
    """Client for interacting with MCP servers"""
    def __init__(self, server_config: Dict[str, Any]):
        self.name = server_config.get('name', '')
        self.command = server_config.get('command')
        self.args = server_config.get('args', [])
        self.url = server_config.get('url')
        self.headers = server_config.get('headers', {})
        self.env = server_config.get('env', {})
        self.tools: List[Dict[str, Any]] = []
        self.resources: List[Dict[str, Any]] = []
        
    async def connect(self):
        """Connect to MCP server and load available tools and resources"""
        if self.url:  # Remote server
            async with aiohttp.ClientSession() as session:
                # List tools
                async with session.get(f"{self.url}/tools", headers=self.headers) as resp:
                    if resp.status == 200:
                        self.tools = await resp.json()
                
                # List resources
                async with session.get(f"{self.url}/resources", headers=self.headers) as resp:
                    if resp.status == 200:
                        self.resources = await resp.json()
        else:  # Local server
            # TODO: Implement local server connection via subprocess
            pass

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Execute a tool on the MCP server"""
        if self.url:  # Remote server
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.url}/tools/{tool_name}",
                    headers=self.headers,
                    json=params
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        raise Exception(f"Error executing tool {tool_name}: {await resp.text()}")
        else:
            # TODO: Implement local server tool execution
            pass

    async def access_resource(self, uri: str) -> Any:
        """Access a resource from the MCP server"""
        if self.url:  # Remote server
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/resources/{uri}",
                    headers=self.headers
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        raise Exception(f"Error accessing resource {uri}: {await resp.text()}")
        else:
            # TODO: Implement local server resource access
            pass

class ToolManager:
    """Manages both local and MCP tools"""
    def __init__(self):
        self.local_tools = []
        self.mcp_clients: Dict[str, McpClient] = {}
        self.load_mcp_config()

    def load_mcp_config(self):
        """Load MCP server configuration"""
        config_path = 'tools/MCP_tools.json'
        try:
            with open(config_path) as f:
                config = json.load(f)
                for name, server_config in config.get('mcpServers', {}).items():
                    if not server_config.get('disabled', False):
                        self.mcp_clients[name] = McpClient(server_config)
        except Exception as e:
            debug_print(MAGENTA, f"Error loading MCP config: {e}")

    def load_local_tools(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Load local tool modules"""
        tools_dir = '../tools'
        tool_instances = []
        
        for tool_name in tool_names:
            try:
                file_path = os.path.join(tools_dir, f'{tool_name}.py')
                spec = importlib.util.spec_from_file_location(tool_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'execute') and hasattr(module, 'get_tool_description'):
                    tool_instances.append({
                        'name': tool_name,
                        'description': module.get_tool_description(),
                        'execute': module.execute,
                        'type': 'local'
                    })
                else:
                    debug_print(MAGENTA, f"Error: Tool {tool_name} lacks required methods.")
            except Exception as e:
                debug_print(MAGENTA, f"Error loading tool {tool_name}: {e}")
        
        return tool_instances

    async def load_mcp_tools(self):
        """Load tools from all configured MCP servers"""
        for client in self.mcp_clients.values():
            try:
                await client.connect()
            except Exception as e:
                debug_print(MAGENTA, f"Error connecting to MCP server {client.name}: {e}")

    def generate_tool_descriptions(self, tool_instances: List[Dict[str, Any]]) -> str:
        """Generate formatted tool descriptions including both local and MCP tools"""
        descriptions = []
        
        # Local tools
        for tool in tool_instances:
            descriptions.append(f"- {tool['name']}: {tool['description']}")
        
        # MCP tools
        for client in self.mcp_clients.values():
            for tool in client.tools:
                descriptions.append(f"- {tool['name']} (MCP): {tool['description']}")
        
        return "\n".join(descriptions)

    def parse_tool_calls(self, tool_response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response"""
        start_index = tool_response.find('[')
        end_index = tool_response.rfind(']')
        
        if start_index == -1 or end_index == -1:
            raise json.JSONDecodeError("No tool calls found", tool_response, 0)
        
        json_string = tool_response[start_index:end_index + 1]
        return json.loads(json_string)

    async def execute_tools(self, tool_calls: List[Dict[str, Any]], tool_instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute both local and MCP tools"""
        results = []
        
        for call in tool_calls:
            tool_name = call.get('tool_name')
            params = call.get('parameters', {})
            
            # Check local tools first
            local_tool = next((t for t in tool_instances if t['name'] == tool_name), None)
            
            if local_tool:
                try:
                    debug_print(BLUE, f"Executing local tool: {tool_name} with params: {params}")
                    result = local_tool['execute'](**params)
                    debug_print(GREEN, f"Tool result: {result}")
                    results.append({"tool_name": tool_name, "tool_params": params, "tool_result": result})
                except Exception as e:
                    debug_print(MAGENTA, f"Error executing local tool {tool_name}: {e}")
                    results.append({"tool_name": tool_name, "error": str(e)})
            else:
                # Check MCP tools
                for client in self.mcp_clients.values():
                    mcp_tool = next((t for t in client.tools if t['name'] == tool_name), None)
                    if mcp_tool:
                        try:
                            debug_print(BLUE, f"Executing MCP tool: {tool_name} with params: {params}")
                            result = await client.execute_tool(tool_name, params)
                            debug_print(GREEN, f"Tool result: {result}")
                            results.append({"tool_name": tool_name, "tool_params": params, "tool_result": result})
                            break
                        except Exception as e:
                            debug_print(MAGENTA, f"Error executing MCP tool {tool_name}: {e}")
                            results.append({"tool_name": tool_name, "error": str(e)})
                else:
                    debug_print(MAGENTA, f"Error: Tool {tool_name} not found.")
                    results.append({"tool_name": tool_name, "error": "Tool not found"})
        
        return results

# Create singleton instance
tool_manager = ToolManager()

# Export functions that maintain the original interface
def load_tools(tool_names):
    return tool_manager.load_local_tools(tool_names)

def generate_tool_descriptions(tool_instances):
    return tool_manager.generate_tool_descriptions(tool_instances)

def parse_tool_calls(tool_response):
    return tool_manager.parse_tool_calls(tool_response)

def execute_tools(tool_calls, tool_instances):
    return asyncio.run(tool_manager.execute_tools(tool_calls, tool_instances))