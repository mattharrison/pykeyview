import sys

import gtk, gtk.glade

import pyxhook

# Want to handle/show these in a nice emacsy way
MODIFIERS = {
    'Control_L':1,
    'Control_R':1,
    'Alt_L':1,
    'Alt_R':1,
    }

# Alter the appearance of some key events
KEY_MAP = {
    'Return':'\n',
    'Control_L':'C-',
    'Control_R':'C-',
    'Alt_L':'M-',
    'Alt_R':'M-',
    'Shift_L':'',
    'Shift_R':'',
    'space': ' ',
    'parenleft': '(',
    'parenright': ')',
    'bracketleft': '[',
    'bracketright': ']',
    'braceleft': '{',
    'braceright': '}',
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
        self.key_strokes.set_alignment(.1, 0)
        self.menu = xml.get_widget('config-menu')
        self.font_dialog = xml.get_widget('fontselectiondialog1')
        self.font = None # text of font description from selection dialog
        self.init_menu()
        self.pressed_modifiers = {} # keep track of whats pushed
        self.hm = hm
        self.active = True
        hm.KeyDown = self.hook_manager_down_event
        hm.KeyUp = self.hook_manager_up_event
        xml.signal_autoconnect(self)
        self.max_lines = 3
        self.show_backspace = False
        self.keys = [] #stack of keys typed

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
            font_desc_text = 'font_desc="%s"' % font_desc
        else:
            font_desc_text = ''
        pango_markup = """<span %s>%s</span>""" % (font_desc_text, text)
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
                
            if event.Key in MODIFIERS:
                self.pressed_modifiers[event.Key] = 1
            elif e_key == 'BackSpace' and not self.show_backspace:
                if self.keys:
                    self.keys.pop()
            else:
                typed = KEY_MAP.get(e_key, e_key)
                self.keys.append(Text(typed, postfix=postfix, prefix=''.join(modifiers)))

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
            
def main():
    gtk.gdk.threads_init() 
    hm = get_hook_manager()
    test = GTKKeyView(hm)
    test.window.show()
    test.window.set_keep_above(True) #ensure visibility
    try:
        gtk.main()
    except KeyboardInterrupt, e:
        # kill the hook manager thread
        test.hm.cancel()

def test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    main()

    
        
