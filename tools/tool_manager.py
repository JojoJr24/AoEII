import curses
import json
import os
import importlib.util

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))

class ToolManagerApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.stdscr.clear()
        self.stdscr.refresh()
        curses.curs_set(0)
        self.height, self.width = stdscr.getmaxyx()
        self.tools = self.load_tools()
        self.current_selection = 0
        self.edit_mode = False
        self.edit_tool_name = ""
        self.edit_tool_modes = ""
        self.edit_tool_description = ""

    def load_tools(self):
        tools = []
        for filename in os.listdir(TOOLS_DIR):
            if filename.endswith(".py") and filename != "__init__.py" and filename != "tool_manager.py":
                try:
                    spec = importlib.util.spec_from_file_location("tool_module", os.path.join(TOOLS_DIR, filename))
                    tool_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(tool_module)
                    if hasattr(tool_module, 'get_tool_description') and hasattr(tool_module, 'modes'):
                        tools.append({
                            "name": filename[:-3],
                            "description": tool_module.get_tool_description(),
                            "modes": tool_module.modes
                        })
                except Exception as e:
                    self.add_message(f"Error loading tool {filename}: {e}", is_user=False)
        return tools

    def display_tools(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Tool Management:")
        for i, tool in enumerate(self.tools):
            prefix = "> " if i == self.current_selection else "  "
            self.stdscr.addstr(i + 2, 3, f"{prefix}{tool['name']}")
        self.stdscr.addstr(len(self.tools) + 3, 1, "a: Add, e: Edit, d: Delete, v: View, q: Quit")
        self.stdscr.refresh()

    def add_message(self, message, is_user=True):
        self.stdscr.addstr(self.height - 2, 1, " " * (self.width - 2))
        self.stdscr.addstr(self.height - 2, 1, message)
        self.stdscr.refresh()

    def add_tool(self):
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "Add Tool:")
        self.stdscr.addstr(2, 3, "Name:")
        self.stdscr.addstr(3, 3, "Modes (comma separated):")
        self.stdscr.refresh()
        curses.echo()
        self.stdscr.move(2, 9)
        tool_name = self.stdscr.getstr(20).decode('utf-8').strip()
        self.stdscr.move(3, 28)
        tool_modes = self.stdscr.getstr(20).decode('utf-8').strip()
        curses.noecho()
        if tool_name and tool_modes:
            if not tool_name.endswith(".py"):
                tool_name += ".py"
            try:
                with open(os.path.join(TOOLS_DIR, tool_name), "w") as f:
                    f.write(f"""
def get_tool_description():
    return \"\"\"
    This is a new tool.
    \"\"\"
modes = {json.dumps([mode.strip() for mode in tool_modes.split(',')])}

def execute():
    pass
""")
                self.tools = self.load_tools()
                self.add_message(f"Tool {tool_name} added successfully.", is_user=False)
            except Exception as e:
                self.add_message(f"Error adding tool: {e}", is_user=False)
        else:
            self.add_message("Tool name and modes are required.", is_user=False)
        self.stdscr.getch()

    def edit_tool(self):
        if not self.tools:
            self.add_message("No tools to edit.", is_user=False)
            self.stdscr.getch()
            return
        if not self.tools:
            self.add_message("No tools to edit.", is_user=False)
            self.stdscr.getch()
            return
        self.edit_mode = True
        selected_tool = self.tools[self.current_selection]
        self.edit_tool_name = selected_tool['name']
        self.edit_tool_modes = ", ".join(selected_tool['modes'])
        self.edit_tool_description = selected_tool['description'].strip()
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, f"Edit Tool: {self.edit_tool_name}")
        self.stdscr.addstr(2, 3, f"Description: {self.edit_tool_description}")
        self.stdscr.addstr(3, 3, f"Modes (comma separated): {self.edit_tool_modes}")
        self.stdscr.refresh()
        curses.echo()
        self.stdscr.move(2, 15)
        tool_description = self.stdscr.getstr(50).decode('utf-8').strip()
        self.stdscr.move(3, 30 + len(self.edit_tool_modes))
        tool_modes = self.stdscr.getstr(50).decode('utf-8').strip()
        curses.noecho()
        if tool_modes and tool_description:
            try:
                with open(os.path.join(TOOLS_DIR, f"{self.edit_tool_name}.py"), "r") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    if line.startswith("modes = "):
                        lines[i] = f"modes = {json.dumps([mode.strip() for mode in tool_modes.split(',')])}\n"
                    if line.strip().startswith('return """'):
                        start_index = i
                        end_index = -1
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().endswith('"""'):
                                end_index = j
                                break
                        if end_index != -1:
                            lines = lines[:start_index+1] + [f'    {tool_description}\n'] + lines[end_index:]
                            break
                with open(os.path.join(TOOLS_DIR, f"{self.edit_tool_name}.py"), "w") as f:
                    f.writelines(lines)
                self.tools = self.load_tools()
                self.add_message(f"Tool {self.edit_tool_name} updated successfully.", is_user=False)
            except Exception as e:
                self.add_message(f"Error editing tool: {e}", is_user=False)
        else:
            self.add_message("Description and Modes are required.", is_user=False)
        self.edit_mode = False
        self.stdscr.getch()

    def delete_tool(self):
        if not self.tools:
            self.add_message("No tools to delete.", is_user=False)
            self.stdscr.getch()
            return
        tool_name = self.tools[self.current_selection]['name']
        try:
            os.remove(os.path.join(TOOLS_DIR, f"{tool_name}.py"))
            self.tools = self.load_tools()
            self.add_message(f"Tool {tool_name} deleted successfully.", is_user=False)
        except Exception as e:
            self.add_message(f"Error deleting tool: {e}", is_user=False)
        self.stdscr.getch()

    def view_tool(self):
        if not self.tools:
            self.add_message("No tools to view.", is_user=False)
            self.stdscr.getch()
            return
        selected_tool = self.tools[self.current_selection]
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, f"Tool: {selected_tool['name']}")
        self.stdscr.addstr(2, 3, f"Description: {selected_tool['description']}")
        self.stdscr.addstr(3, 3, f"Modes: {', '.join(selected_tool['modes'])}")
        self.stdscr.refresh()
        self.stdscr.getch()

    def run(self):
        while True:
            self.display_tools()
            key = self.stdscr.getch()
            if key == curses.KEY_UP and self.current_selection > 0:
                self.current_selection -= 1
            elif key == curses.KEY_DOWN and self.current_selection < len(self.tools) - 1:
                self.current_selection += 1
            elif key == ord('a'):
                self.add_tool()
            elif key == ord('e'):
                self.edit_tool()
            elif key == ord('d'):
                self.delete_tool()
            elif key == ord('v'):
                self.view_tool()
            elif key == ord('q'):
                break

def main(stdscr):
    app = ToolManagerApp(stdscr)
    app.run()

if __name__ == '__main__':
    curses.wrapper(main)
