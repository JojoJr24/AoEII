# Integration Plan: Local and MCP Tools

This document outlines the plan to integrate MCP tools seamlessly with existing local tools in `backend/tool_manager.py`.

## 1. Analyze the Existing Code:

*   Understand how local tools are loaded, described, parsed, and executed.
*   Understand how MCP tools are loaded, described, parsed, and executed.
*   Identify the data structures used to represent tools (local and MCP).
*   Pinpoint the functions responsible for tool loading, description generation, parsing, and execution.

## 2. Load MCP Tools:

*   Modify `ToolManager.load_mcp_config()` to load MCP server configurations from `tools/MCP_tools.json`.
*   Completely ignore servers where the `disabled` flag is set to `true`.
*   Implement the `McpClient.connect()` method to connect to both remote and local MCP servers.
    *   For remote servers, use `aiohttp` to fetch tool and resource lists.
    *   For local servers, use a specific port for communication. The port should be configurable in `MCP_tools.json`.
*   Implement the `McpClient.execute_tool()` method to execute tools on both remote and local MCP servers.
    *   For remote servers, use `aiohttp` to send tool execution requests.
    *   For local servers, use a specific port for communication.
*   Implement the `McpClient.access_resource()` method to access resources from both remote and local MCP servers.
    *   For remote servers, use `aiohttp` to fetch resources.
    *   For local servers, use a specific port for communication.
*   Modify `ToolManager.load_mcp_tools()` to connect to all configured MCP servers and load their tools.

## 3. Merge Local and MCP Tools:

*   Modify `ToolManager` to store both local tools and MCP tools in a unified data structure.
*   Prefix all MCP tool names with "mcp\_" to avoid naming conflicts with local tools.

## 4. Generate Tool Descriptions:

*   Modify `ToolManager.generate_tool_descriptions()` to include descriptions for both local and MCP tools.

## 5. Parse Tool Calls:

*   Ensure that `ToolManager.parse_tool_calls()` can correctly parse tool calls for both local and MCP tools.
*   The current implementation uses string manipulation to find the tool calls. This could be made more robust by using a regex.

## 6. Execute Tools:

*   Modify `ToolManager.execute_tools()` to handle both local and MCP tools.
*   First, check if the tool is a local tool. If so, execute it as before.
*   If the tool is not a local tool, check if it is an MCP tool (by checking if the tool name starts with "mcp\_"). If so, execute it using the appropriate `McpClient`.
*   Handle errors gracefully and return appropriate results.

## 7. Maintain Backward Compatibility:

*   Ensure that the existing public interface (`load_tools()`, `generate_tool_descriptions()`, `parse_tool_calls()`, `execute_tools()`) remains unchanged.
*   Existing code that uses local tools should continue to work without modification.

## 8. Testing:

*   Write unit tests to verify that local tools continue to work as expected.
*   Write integration tests to verify that MCP tools are loaded, described, parsed, and executed correctly.
*   Test both remote and local MCP servers.
*   Test error handling.

## Diagram

```mermaid
graph TD
    A[Start] --> B{Load local tools};
    B --> C{Load MCP tools from MCP_tools.json (ignore disabled servers)};
    C --> D{Merge local and MCP tools (prefix MCP tools with "mcp_")};
    D --> E{Generate tool descriptions};
    E --> F{Parse tool calls};
    F --> G{Execute tools};
    G --> H{Return results};
    H --> I[End];