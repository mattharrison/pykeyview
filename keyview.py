#!/usr/bin/env python
# -*- coding: utf-8 -*-
from xml.sax.saxutils import escape, quoteattr
import gtk, gtk.glade
from time import time

import pyxhook

# Want to handle/show these in a nice emacsy way
MODIFIERS = (
    'Control_L',
    'Control_R',
    'Alt_L',
    'Alt_R',
    'Super_L',
    'Mode_switch'    
)

CHORD_PREFIXES = (
    'f1-',
    'f2-'
)

SHIFT_KEYS = (
    'Shift_L',
    'Shift_R',
)

# Alter the appearance of some key events
KEY_MAP = {
    'F1':'f1-',
    'F2':'f2-',
    'F3':'f3',
    'F4':'f4',
    'F5':'f5',
    'F6':'f6',
    'F7':'f7',
    'F8':'f8',
    'F9':'f9',
    'F10':'f10',
    'F11':'f11',
    'F12':'f12',
    'Return':'↲',
    'Right': '→',
    'Left': '←',
    'Up': '↑',
    'Down': '↓',
    'Control_L':'Ctrl-',
    'Control_R':'Ctrl-',
    'Mode_switch':'Mod4-',
    'Alt_L':'Alt-',
    'Alt_R':'Alt-',
    'Shift_L':'⇪-',
    'Shift_R':'⇪-',
    'space': ' ',
    'parenleft': '(',
    'parenright': ')',
    'bracketleft': '[',
    'bracketright': ']',
    'braceleft': '{',
    'braceright': '}',
    'BackSpace': '⇤',
    'Delete': 'DEL',
    'Tab': '↹',
    'bar': '|',
    'minus': '-',
    'plus': '+',
    'asterisk': '*',
    'equal': '=',
    'less': '<',
    'greater': '>',
    'semicolon': ';',
    'colon': ':',
    'comma': ',',
    'apostrophe': "'",
    'quotedbl' : '"',
    'underscore' : '_',
    'numbersign' : '#',
    'percent' : '%',
    'exclam' : '!',
    'period' : '.',
    'slash' : '/',
    'backslash' : '\\',
    'question' : '?',
    'adiaeresis': 'ä',
    'odiaeresis': 'ö',
    'udiaeresis': 'ü',
    'ssharp': 'ß',
    'ampersand': '&',
    'section': '§',
}

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


class GTKKeyView:
    def __init__(self, hm):

        xml = gtk.glade.XML('keyview.libglade')
        self.window = xml.get_widget('window1')
        self.window.connect('destroy', self.quit)
        self.key_strokes = xml.get_widget('label1')
        self.key_strokes.set_alignment(0, 0)
        self.menu = xml.get_widget('config-menu')
        self.font_dialog = xml.get_widget('fontselectiondialog1')
        self.font = 'Courier Bold 30' #None # text of font description from selection dialog
        self.init_menu()
        self.pressed_modifiers = {} # keep track of whats pushed
        self.hm = hm
        self.active = True
        hm.KeyDown = self.hook_manager_down_event
        hm.KeyUp = self.hook_manager_up_event
        xml.signal_autoconnect(self)
        self.max_lines = 3
        self.show_backspace = True
        self.show_shift = False
        self.keys = [] #stack of keys typed
        self.last_key = 0 # keep track of time

    def init_menu(self):
        self.font_item = gtk.MenuItem('set font...')
        self.font_item.connect('activate', self.font_select)

        self.on_item = gtk.CheckMenuItem('listening')
        self.on_item.set_active(True)
        self.on_item.connect('activate', self.toggle_active)

        self.quit_item = gtk.MenuItem('quit')
        self.quit_item.connect('activate', self.quit)

        for item in [self.font_item, self.on_item, self.quit_item]:
            self.menu.append(item)
            item.show()

    def font_select(self, widget):
        response = self.font_dialog.run()
        self.font_dialog.hide()
        self.font = self.font_dialog.get_font_name()
        cur_text = self.key_strokes.get_text()
        self.update_text(cur_text, self.font)


    def toggle_active(self, widget):
        # active is state after click
        self.active = widget.get_active()


    def quit(self, widget):
        self.hm.cancel()
        gtk.main_quit()


    def on_eventbox1_popup_menu(self, *args):
        self.menu.show()

    def on_eventbox1_button_press_event(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.menu.popup(None, None, None, event.button, event.get_time())

    def update_text(self, text, font_desc=None):
        """
        see
        http://www.pygtk.org/docs/pygtk/class-gtklabel.html
        and
        http://www.pygtk.org/docs/pygtk/pango-markup-language.html
        """
        if font_desc:
            font_desc_text = 'font_desc=%s' % quoteattr(font_desc)
        else:
            font_desc_text = ''
        pango_markup = """<span %s>%s</span>""" % (font_desc_text, escape(text))
        self.key_strokes.set_markup(pango_markup)

    def hook_manager_up_event(self, event):
        if event.Key in self.pressed_modifiers:
            del self.pressed_modifiers[event.Key]

    def hook_manager_down_event(self, event):
        #hm.printevent(event)
        if self.active:
            e_key = event.Key

            # hack to deal with ctr modifiers in emacsy way
            modifiers = []
            postfix = ''
            for modifier in self.pressed_modifiers.keys():
                mod = KEY_MAP.get(modifier, modifier)
                if self.keys and not self.keys[-1].text == mod:
                    modifiers.append(mod)
                postfix = ' '

            if e_key in MODIFIERS:
                self.pressed_modifiers[e_key] = 1
            elif e_key == 'BackSpace' and not self.show_backspace:
                if self.keys:
                    self.keys.pop()
            elif e_key in SHIFT_KEYS:
                if self.show_shift:
                    self.pressed_modifiers[e_key] = 1
            else:
                txt = KEY_MAP.get(e_key, e_key)

                prefix = ''.join(modifiers)
                txt = Text(txt, prefix, postfix)

                isseq = (
                    len(self.keys) > 0 and
                    (self.keys[-1].is_chord_prefix
                    or
                    self.keys[-1].is_char and time() - self.last_key < 1)
                )

                if not (txt.is_char and isseq):
                    self.keys.append(Text("\n"))

                self.keys.append(txt)

                self.last_key = time()


            # limit line lengths
            self.keys = limit_text(self.keys, self.max_lines)
            new_text = ''.join([repr(x) for x in self.keys])

            self.update_text(new_text, self.font)

def limit_text(text_list, max_lines):
    r"""
    >>> lines = [Text('\n')]*4
    >>> len(limit_text(lines, 2)) #only 1 newline is possible since we're limiting to two lines
    1
    >>> lines = [Text(x) for x in 'foo\nbar\nbaz']
    >>> len(limit_text(lines, 2)) #from bar to end
    7

    """
     # limit line lengths
    new_line_idx = [i for i,x in enumerate(text_list) if x.text == '\n']
    if len(new_line_idx) >= max_lines:
        new_start = new_line_idx[-max_lines] + 1
        text_list = text_list[new_start:]
    return text_list

class Text(object):
    """Simple class to hold text and pre/postfix for it
    """
    def __init__(self, text, prefix='', postfix=''):
        self.text = text
        self.prefix = prefix
        self.postfix = postfix

    def __repr__(self):
        return '%s%s%s' %(self.prefix, self.text, self.postfix)

    @property
    def is_char(self):
        t = self.text
        return len(t) == 1 and (t.isalnum() or t.isspace())
    @property
    def is_chord_prefix(self):
        return self.text in CHORD_PREFIXES

def main():
    gtk.gdk.threads_init()
    hm = get_hook_manager()
    view = GTKKeyView(hm)
    w = view.window
    w.resize(360, 150)
    w.set_keep_above(True) #ensure visibility
    w.show()

    try:
        gtk.main()
    except KeyboardInterrupt, e:
        # kill the hook manager thread
        view.hm.cancel()

def test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    main()



