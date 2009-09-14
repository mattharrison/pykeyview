import sys

import gtk, gtk.glade

import pyxhook

def get_hook_manager():
    hm = pyxhook.HookManager()
    hm.HookKeyboard()
    hm.HookMouse()
    #hm.KeyDown = hm.printevent
    #hm.KeyUp = self.hook_manager_event #hm.printevent
    #hm.MouseAllButtonsDown = hm.printevent
    #hm.MouseAllButtonsUp = hm.printevent
    hm.start()
    return hm

class SimpleTest:
    def __init__(self, hm):
        xml = gtk.glade.XML('keyview.libglade')
        self.window = xml.get_widget('window1')
        self.key_strokes = xml.get_widget('label1')
        self.menu = xml.get_widget('config-menu')
        self.init_menu()
        self.hm = hm
        hm.KeyDown = self.hook_manager_event
        xml.signal_autoconnect(self)
        self.max_size = 10

    def init_menu(self):
        self.font_item = gtk.MenuItem('set font...')
        self.on_item = gtk.MenuItem('off')
        self.quit_item = gtk.MenuItem('quit')
        for item in [self.font_item, self.on_item, self.quit_item]:
            self.menu.append(item)
            item.show()

    def on_eventbox1_popup_menu(self, *args):
        self.menu.show()

    def on_eventbox1_button_press_event(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.menu.popup(None, None, None, event.button, event.get_time())
        
        
    def hook_manager_event(self, event):
        old = self.key_strokes.get_text()
        new_text = (old + event.Key)[-self.max_size:]
        self.key_strokes.set_text(new_text)


    
gtk.gdk.threads_init() 
hm = get_hook_manager()
test = SimpleTest(hm)
test.window.show()
gtk.main()
