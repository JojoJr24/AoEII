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
        self.stdscr.addstr(len(self.tools) + 3, 1, "v: View, q: Quit")
        self.stdscr.refresh()

    def add_message(self, message, is_user=True):
        self.stdscr.addstr(self.height - 2, 1, " " * (self.width - 2))
        self.stdscr.addstr(self.height - 2, 1, message)
        self.stdscr.refresh()

    def wrap_text(self, text, width):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) + 1 <= width:
                current_line += (word + " ")
            else:
                lines.append(current_line.rstrip())
                current_line = word + " "
        lines.append(current_line.rstrip())
        return lines

    def view_tool(self):
        if not self.tools:
            self.add_message("No tools to view.", is_user=False)
            self.stdscr.getch()
            return
        selected_tool = self.tools[self.current_selection]
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, f"Tool: {selected_tool['name']}")
        
        description_lines = self.wrap_text(f"Description: {selected_tool['description']}", self.width - 4)
        y = 2
        for line in description_lines:
            self.stdscr.addstr(y, 3, line)
            y += 1
        
        self.stdscr.addstr(y, 3, f"Modes: {', '.join(selected_tool['modes'])}")
        self.stdscr.addstr(y + 1, 3, f"File: {selected_tool['name']}.py")
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
            elif key == ord('v'):
                self.view_tool()
            elif key == ord('q'):
                break

def main(stdscr):
    app = ToolManagerApp(stdscr)
    app.run()

if __name__ == '__main__':
    curses.wrapper(main)
