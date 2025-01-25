import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import os
import json
import requests
import io
import torch
import cairo
from TTS.api import TTS

class FloatingButton:
    def __init__(self):
        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.set_app_paintable(True)
        screen = Gdk.Screen.get_default()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)
        self.window.connect("draw", self.on_draw)
        self.button = Gtk.Button(label="Asistente")
        self.button.connect("clicked", self.on_button_clicked)
        self.window.add(self.button)
        self.window.show_all()
        self.window.move(10, 10)
        self.text_window = None

        # Initialize the TTS engine
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS(model_name="tts_models/es/css10/vits", progress_bar=False)
        self.tts.to(device)

    def wrap_text(self, text, width):
        """Wraps text to a given width."""
        import textwrap
        wrapped_text = textwrap.fill(text, width=width)
        return wrapped_text

    def on_draw(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(1)
        cr.paint()

    def on_button_clicked(self, widget):
        if self.text_window is None:
            self.text_window = Gtk.Window()
            self.text_window.set_title("Asistente")
            self.text_window.set_default_size(400, 300)

            # Create a box to hold the text area and the button
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

            self.text_area = Gtk.TextView()
            self.text_buffer = self.text_area.get_buffer()
            scroll = Gtk.ScrolledWindow()
            scroll.add(self.text_area)
            box.pack_start(scroll, True, True, 0)

            # Create the send button
            send_button = Gtk.Button(label="Send")
            send_button.connect("clicked", self.on_send_clicked)
            box.pack_start(send_button, False, False, 0)

            self.text_window.add(box)
            self.text_window.show_all()
            self.text_window.connect("destroy", self.on_text_window_destroy)
        else:
            self.text_window.present()

    def on_send_clicked(self, widget):
        # Minimize the text window
        original_size = self.text_window.get_size()
        self.text_window.iconify()

        # Wait for the text window to be minimized
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Get the root window
        window = Gdk.get_default_root_window()
        if not window:
            print("No root window found")
            return

        # Get the screen size
        width = window.get_width()
        height = window.get_height()

        # Create a pixbuf from the window
        pixbuf = Gdk.pixbuf_get_from_window(window, 0, 0, width, height)
        if not pixbuf:
            print("No pixbuf found")
            return

        # Create a cairo surface from the pixbuf
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
        context = cairo.Context(surface)
        Gdk.cairo_set_source_pixbuf(context, pixbuf, 0, 0)
        context.paint()

        # Save the surface to a PNG file
        image_stream = io.BytesIO()
        surface.write_to_png(image_stream)
        image_stream.seek(0)

        # Get the text from the text area
        text_buffer = self.text_area.get_buffer()
        text = text_buffer.get_text(text_buffer.get_start_iter(), text_buffer.get_end_iter(), True)

        # Load the configuration from console/config.json
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                selected_provider = config.get("selected_provider", "gemini")
                selected_model = config.get("selected_model", "models/gemini-2.0-flash-exp")
                selected_system_message_id = config.get("selected_system_message_id")
        except Exception as e:
            print(f"Error loading config: {e}")
            return

        system_message = None
        if selected_system_message_id:
            try:
                response = requests.get(f"http://127.0.0.1:5000/api/system_messages/{selected_system_message_id}")
                if response.status_code == 200:
                    system_message = response.json().get('content')
                else:
                    print(f"Error fetching system message: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error fetching system message: {e}")

        # Prepare the request data
        files = {'image': ('screenshot.png', image_stream, 'image/png')}
        data = {
            'prompt': text,
            'provider': selected_provider,
            'model': selected_model,
            'system_message': system_message
        }

        # Send the request to the /generate endpoint
        try:
            response = requests.post("http://127.0.0.1:5000/api/generate", files=files, data=data, stream=True)
            if response.status_code == 200:
                complete_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            json_data = json.loads(line.strip())
                            response_text = json_data.get('response', '')
                            print(response_text)
                            complete_response += response_text + " "
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON: {line}")

                # Once the entire response is received, synthesize it
                if complete_response.strip():
                    self.tts.tts_to_file(text=complete_response.strip(), file_path="output.wav")
                    os.system("aplay output.wav")
                    # Restore the text window size
                    self.text_window.set_default_size(original_size[0], original_size[1])
                    self.text_window.present()
                    # Get the text area width
                    text_area_width = self.text_area.get_allocated_width()
                    # Wrap the response text
                    wrapped_response = self.wrap_text(complete_response, text_area_width)
                    # Insert the response into the text area
                    self.text_buffer.insert(self.text_buffer.get_end_iter(), "\n" + wrapped_response)
                else:
                    print("Complete response is empty, skipping TTS.")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending request: {e}")

    def on_text_window_destroy(self, widget):
        self.text_window = None

    def run(self):
        Gtk.main()

if __name__ == '__main__':
    button = FloatingButton()
    button.run()
