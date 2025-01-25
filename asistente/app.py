import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import os
import cairo

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
        surface.write_to_png("screenshot.png")
        print("Screenshot saved to screenshot.png")

    def on_text_window_destroy(self, widget):
        self.text_window = None

    def run(self):
        Gtk.main()

if __name__ == '__main__':
    button = FloatingButton()
    button.run()
