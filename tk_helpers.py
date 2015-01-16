"""
tk_helpers.py

@author: James Fowkes

Defines some helper classes to abstract away some generic processing for Tk GUI objects

"""

import tkinter as Tk
from tkinter import ttk

# pylint: disable=too-many-ancestors
# pylint: disable=star-args
class TkOptionMenuHelper(Tk.OptionMenu):

    """
    A helper class to abstract away the slightly messy
    business of handling an option menu, its entries and current values

    pylint too-many-ancestors check is disabled for this class, since nothing
    can be done about the Tk inheritance tree.
    pylint star-args check is disabled for this class, since this is how args are
    passed to the Tk object
    """

    def __init__(self, master, title, options, command, width=15): # pylint: disable=too-many-arguments

        """
        Args:
        master: The tkinter master that will be the parent container of the control
        title: The string that will be displayed when the control is first loaded
        options: Dictionary of options to pass to the option menu constructor
        command: Function that will be called when an option is selected
        width: The width of the control

        pylint too-many-arguments check is disabled for this class. All the arguments are required.
        """

        self.master = master
        self.title = title
        self.application_callback = command
        self.width = width

        self.var = Tk.StringVar(master)
        self.var.set(title)

        Tk.OptionMenu.__init__(self, master, self.var, *options, command=self.on_var_change)
        self.config(width=width)

    def on_var_change(self, new_var):

        """
        Callback that is invoked by the control.
        Sets the class StringVar and calls application callback.
        Args:
        new_var: The selection made
        """

        if new_var != self.title:
            self.var.set(new_var)
            if self.application_callback is not None:
                self.application_callback(new_var)

    def set_options(self, new_options):
        """ Sets new menu options. """

        self['menu'].delete(0, "end")
        for opt in new_options:
            self['menu'].add_command(label=opt, command=lambda val=opt: self.on_var_change(val))
        self.var.set(self.title)

#pylint: disable=too-few-public-methods
#pylint: disable=too-many-ancestors
class TkEntryHelper(Tk.Entry):
    """
    A small class to abstract away the attachment of a Tk.StringVar to an entry box

    pylint too-many-ancestors check is disabled for this class, since nothing
    can be done about the Tk inheritance tree.

    pylint too-few-public-methods check is disabled for this class. This is meant to be
    a small helper class.
    """
    def __init__(self, master, **kwargs):
        """
        Args:
        master: The tkinter master that will be the parent container of the control
        kwargs: Any additional keyword arguments
        """
        self.var = Tk.StringVar(master)
        Tk.Entry.__init__(self, master, textvariable=self.var, **kwargs)

#pylint: disable=too-few-public-methods
#pylint: disable=too-many-ancestors
#pylint: disable=star-args
class TkLabelledEntryHelper(TkEntryHelper):
    """
    A small class to abstract away the attachment of a label to an entry box

    pylint too-many-ancestors check is disabled for this class, since nothing
    can be done about the Tk inheritance tree.

    pylint too-few-public-methods check is disabled for this class. This is meant to be
    a small helper class.

    pylint star-args check is disabled for this class, since this is how args are
    passed to the Tk object
    """

    def __init__(self, master, label_text, label_pack_kwargs, **kwargs):
        """
        Args:
        master: The tkinter master that will be the parent container of the control
        label: The Tkinter label for the entry
        label_pack_kwargs : Any kwargs that should be used for the label packing
        kwargs: Any additional keyword arguments
        """
        self.label = Tk.Label(master, label_text)
        self.label_pack_kwargs = label_pack_kwargs
        TkEntryHelper.__init__(self, master, **kwargs)

    def pack(self, **kwargs):
        """
        Overrides the Tk pack() method to also pack the label
        """
        self.label.pack(**self.label_pack_kwargs)
        TkEntryHelper.pack(self, **kwargs)

#pylint: disable=too-few-public-methods
#pylint: disable=too-many-ancestors
#pylint: disable=star-args
class TkProgressBarHelper(ttk.Progressbar):
    """
    A small class to abstract away the attachment of a label to a progress bar

    pylint too-many-ancestors check is disabled for this class, since nothing
    can be done about the Tk inheritance tree.

    pylint too-few-public-methods check is disabled for this class. This is meant to be
    a small helper class.

    pylint star-args check is disabled for this class, since this is how args are
    passed to the Tk object
    """

    def __init__(self, master, label_text, label_pack_kwargs, **kwargs):
        """
        Args:
        master: The tkinter master that will be the parent container of the control
        label: The Tkinter label for the progress bar
        label_pack_kwargs : Any kwargs that should be used for the label packing
        kwargs: Any additional keyword arguments
        """
        self.label = Tk.Label(master, label_text)
        self.label_pack_kwargs = label_pack_kwargs
        self.var = Tk.IntVar()
        ttk.Progressbar.__init__(self, master, variable=self.var, **kwargs)

    def pack(self, **kwargs):
        """
        Overrides the Tk pack() method to also pack the label
        """
        self.label.pack(**self.label_pack_kwargs)
        ttk.Progressbar.pack(self, **kwargs)

    def set_label(self, new_text):
        """ Change the progress bar text """
        self.label.config(text=new_text)
        
    def set(self, percent):
        """ Pass new percent through to var """
        self.var.set(percent)
