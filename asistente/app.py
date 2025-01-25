import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import os

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
            self.text_area = Gtk.TextView()
            self.text_buffer = self.text_area.get_buffer()
            scroll = Gtk.ScrolledWindow()
            scroll.add(self.text_area)
            self.text_window.add(scroll)
            self.text_window.show_all()
            self.text_window.connect("destroy", self.on_text_window_destroy)
        else:
            self.text_window.present()

    def on_text_window_destroy(self, widget):
        self.text_window = None

    def run(self):
        Gtk.main()

if __name__ == '__main__':
    button = FloatingButton()
    button.run()
