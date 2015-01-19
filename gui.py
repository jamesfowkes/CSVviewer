"""
gui.py

@author: James Fowkes

Defines a GUI for the CSV viewer application

"""

import os
import logging

import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import tkinter as Tk
from tkinter import messagebox, filedialog

from app_reqs import REQS

from tk_helpers import TkOptionMenuHelper, TkLabelledEntryHelper, TkProgressBarHelper
import app_info

def run_gui():
    """ Entry point into the GUI, from which there is no return until _exit() is called """
    Tk.mainloop()

def get_module_logger():

    """ Returns logger for this module """
    return logging.getLogger(__name__)

def ask_directory(title):
    """
    Brings up Tk askdirectory window and returns resulting path
    Args:
    title: The title for the askdirectory dialog
    """

    return filedialog.askdirectory(title=title)

def show_info_dialog(text):
    """
    Show a Tk messagebox
    Args:
    text: The text to show
    """
    messagebox.showinfo(app_info.TITLE, text)

#pylint: disable=too-many-instance-attributes
class GUI:

    """
    The main GUI for the CSV viewer application
    pylint too-many-instance-attributes warning is disabled.
    This is a big class and probably doesn't benefit from being further broken up.
    """

    #pylint: disable=too-few-public-methods
    class TkHandleCollection:

        """
        A simple object to store the various objects of a Tk window.
        pylint too-few-public-methods is disabled as this is just for storing the Tk objects
        """

        def __init__(self):
            """
            Each window has a window object and a master frame.
            It may also have a canvas, toolbar and figure
            """
            self.windows = {}
            self.frames = {}
            self.canvases = {}
            self.toolbars = {}
            self.figures = {}

    class SubplotSelectDropdowns:

        """ Implements three dropdown menus for picking subplots """

        def __init__(self, master, actions, titles, label):
            """
            Args:
            master : The Tk frame to draw pickers on
            actions: List of action functions to call when selection changes
            titles: List of titles for the dropdowns
            label: A label for the pickers
            """

            self.dropdowns = [
                TkOptionMenuHelper(master, titles[i], [titles[i]], command=actions[i]) for i in range(3)]
            self.current_subplot_names = [None, None, None]
            self.label = label

        # pylint: disable=star-args
        def pack(self, **kwargs):
            """
            Draws the dropdowns on the frame
            pylint star-args check is disabled for this class, since this is how args are
            passed to the Tk object

            Args:
            kwargs: Any Tk options for the dropdowns
            """
            self.label.pack(**kwargs)
            for dropdown in self.dropdowns:
                dropdown.pack(**kwargs)

        def set_display_name(self, index, display_name):
            """
            For each plot, one dataset will be displayed on it at a time
            This display name should NOT be shown in the dropdown for that plot
            Hence, the displayed field is recorded so it can be eliminated in refresh_subplot_lists
            Args:
            index: Index of the subplot (0 to 2)
            display_name: Name of the currently displayed dataset
            """
            self.current_subplot_names[index] = display_name

        def refresh_subplot_lists(self, datasets):
            """
            For each plot, one dataset will be displayed on it at a time
            This display name should NOT be shown in the dropdown for that plot
            This function eliminates the dataset from the list and adds a "None" options
            Args:
            datasets : Full list of datasets that needs filtering per dropdown
            """
            datasets.append("None")
            for i in range(3):
                dataset_list = [dataset for dataset in datasets if dataset != self.current_subplot_names[i]]
                self.dropdowns[i].set_options(dataset_list)

    class DatasetControls:

        """ Handles Tk objects and processing for selecting averaging options for a dataset """

       #pylint: disable=too-many-arguments
        def __init__(
                self, subplot_select_dropdowns, dataset_dropdown,
                average_text_entry, average_period_dropdown, average_button, average_reset_button,
                special_option_dropdown, special_option_button):
            """
            Args:
            master: The frame to draw on
            subplot_select_dropdowns: The three dropdowns for selecting subplots
            dataset_dropdown: The dataset selection dropdown
            average_text_entry: The text entry for entering the time value
            average_period_dropdown: The dropdown to select a time period
            average_button: The button to apply selected averaging
            average_reset_button: The button to reset averaging (display raw data)
            special_option_dropdown: The dropdown to select any special operations to perform
            special_option_button: The button to perform and special operations

            pylint too-many-arguments is disabled. This is a simple container class.
            """
            self.subplot_select_dropdowns = subplot_select_dropdowns
            self.dataset_dropdown = dataset_dropdown
            self.average_text_entry = average_text_entry
            self.average_period_dropdown = average_period_dropdown
            self.average_button = average_button
            self.average_reset_button = average_reset_button
            self.special_option_dropdown = special_option_dropdown
            self.special_option_button = special_option_button

        def get_subplot_list(self):
            """ Return a list of selected subplots """
            return self.subplot_select_dropdowns.current_subplot_names
            
        def get_dataset_name(self):
            """ Return the name of the currently selected dataset """
            return self.dataset_dropdown.var.get()

        def get_averaging_time_period(self):
            """ Return the time value from the text entry """
            return float(self.average_text_entry.var.get())

        def get_averaging_time_units(self):
            """ Returns the selected averaging period (seconds, minutes etc.) """
            return self.average_period_dropdown.var.get()

        def get_special_action(self):
            """ Returns the current selected special action """
            return self.special_option_dropdown.var.get()

        def set_dataset_choices(self, datasets):
            """ Sets the dataset dropdown options """
            self.dataset_dropdown.set_options(datasets)

        def set_special_options(self, options, **kwargs):
            """ Set the special options (or hide the dropdown if None """
            if options is not None:
                self.special_option_dropdown.set_options(options)
                self.special_option_dropdown.pack(**kwargs)
                self.special_option_button.pack(**kwargs)
            else:
                self.special_option_dropdown.pack_forget()
                self.special_option_button.pack_forget()

        def pack(self, **kwargs): #pylint: disable=star-args
            """ Draws the objects on the frame """
            self.dataset_dropdown.pack(**kwargs)
            self.average_text_entry.pack(**kwargs)
            self.average_period_dropdown.pack(**kwargs)
            self.average_button.pack(**kwargs)
            self.average_reset_button.pack(**kwargs)

        def pack_subplot_controls(self, **kwargs): #pylint: disable=star-args
            """ Passes pack request through to subplot object """
            self.subplot_select_dropdowns.pack(**kwargs)

        def set_subplot_display_name(self, index, display_name):
            """ Sets the display name for a subplot """
            self.subplot_select_dropdowns.set_display_name(index, display_name)

        def refresh_subplot_lists(self, datasets):
            """ Pass refresh request to subplot dropdowns object """
            self.subplot_select_dropdowns.refresh_subplot_lists(datasets)
            self.set_dataset_choices(self.subplot_select_dropdowns.current_subplot_names)

        def get_subplot_index_for_dataset(self, dataset):
            """
            Returns the index (0 to 2) of the plot with the requested dataset.
            Returns None if the requested dataset is not currently displayed
            """
            try:
                return self.subplot_select_dropdowns.current_subplot_names.index(dataset)
            except ValueError:
                return None

    class MainWindowFrameCollection:
        """ Implements a collection of frames for the main GUI window """
        #pylint: disable=too-many-arguments
        def __init__(
                self, application_frame, control_frame, plot_select_frame,
                data_controls_frame, data_controls_subframes):
            """
            Args:
            application_frame: Frame containing the Open/About/Exit buttons
            control_frame: Frame containing all the "data" based controls
            plot_select_frame: Frame containing the plotting dataset dropdowns
            data_controls_frame: Frame containing the data_controls_subframes frames
            data_controls_subframes: List of 3 frames containing the individual dataset controls

            pylint too-many-arguments is disabled. This is a simple container class.
            """

            self.application = application_frame
            self.control = control_frame
            self.plot_select = plot_select_frame
            self.data_controls = data_controls_frame
            self.data_controls_subframes = data_controls_subframes

    def __init__(self, req_handler):

        """
        Args:
        application : application object used for querying things like dataset names
        """

        self.application_request = req_handler
        self.root = Tk.Tk()

        # Note: keeping PhotoImage in self.icon stops it being garbage collected.
        # Therefore, don't simplify these lines by getting rid of self.icon!
        self.icon = Tk.PhotoImage(file=os.path.join(app_info.app_dir(), "logo.png"))
        self.root.iconphoto(True, self.icon)

        self.root.wm_title(app_info.TITLE)
        self.root.protocol("WM_DELETE_WINDOW", self._exit)

        get_module_logger().setLevel(logging.INFO)

        self.tk_handles = self.TkHandleCollection()

        application_frame = Tk.Frame(self.root, bd=1, relief=Tk.SUNKEN)
        control_frame = Tk.Frame(self.root, bd=1, relief=Tk.SUNKEN)

        plot_select_frame = Tk.Frame(control_frame)
        data_controls_frame = Tk.Frame(control_frame)

        data_controls_subframes = [
            Tk.Frame(data_controls_frame),
            Tk.Frame(data_controls_frame),
            Tk.Frame(data_controls_frame)]

        self.main_window_frames = self.MainWindowFrameCollection(
            application_frame=application_frame,
            control_frame=control_frame,
            plot_select_frame=plot_select_frame,
            data_controls_frame=data_controls_frame,
            data_controls_subframes=data_controls_subframes)

        # Subplot dataset pickers and label
        subplot_select_dropdowns = self.SubplotSelectDropdowns(
            self.main_window_frames.plot_select,
            [
                lambda sel: self.application_request(REQS.CHANGE_SUBPLOT1, sel),
                lambda sel: self.application_request(REQS.CHANGE_SUBPLOT2, sel),
                lambda sel: self.application_request(REQS.CHANGE_SUBPLOT3, sel),
            ],
            ["Upper Plot Data", "Middle Plot Data", "Lower Plot Data"],
            Tk.Label(self.main_window_frames.plot_select, text="Select plots:"))

        # Dataset selection, averaging and special options
        self.dataset_controls = self.DatasetControls(
            subplot_select_dropdowns,
            TkOptionMenuHelper(
                self.main_window_frames.data_controls_subframes[1], "Select dataset",
                ["Select dataset"], command=self.change_dataset_selection),
            TkLabelledEntryHelper(
                self.main_window_frames.data_controls_subframes[1],
                {"text":"Average every:"},
                {"side":Tk.LEFT, "padx":2, "pady":2},
                width=10),
            TkOptionMenuHelper(
                self.main_window_frames.data_controls_subframes[1], "Seconds",
                ["Seconds", "Minutes", "Hours", "Days", "Weeks"], command=None, width=10),
            Tk.Button(
                self.main_window_frames.data_controls_subframes[1],
                text='Apply',
                command=lambda: self.application_request(REQS.AVERAGE_SUBPLOT_DATA)),
            Tk.Button(
                self.main_window_frames.data_controls_subframes[1],
                text='Reset',
                command=lambda: self.application_request(REQS.RESET_SUBPLOT_DATA)),
            TkOptionMenuHelper(
                self.main_window_frames.data_controls_subframes[2],
                "Special Options", ["Special Options"], command=None),
            Tk.Button(
                self.main_window_frames.data_controls_subframes[2],
                text='Show',
                command=lambda: self.application_request(REQS.SPECIAL_ACTION))
        )

        self.progress_bar = None

        self.ui_exists = False

        self.add_new_window('Main', (8, 5))

        self.new_data_button = Tk.Button(
            self.main_window_frames.application,
            text='Open CSV Folder',
            command=lambda: self.application_request(REQS.NEW_DATA))

        self.new_data_button.pack(padx=10, pady=10)

        self.about_button = Tk.Button(
            self.main_window_frames.application,
            text='About CSV Viewer',
            command=lambda: self.application_request(REQS.ABOUT_DIALOG))

        self.about_button.pack(padx=10, pady=10)

        self.exit_button = Tk.Button(self.main_window_frames.application, text='Exit', command=self._exit)
        self.exit_button.pack(padx=10, pady=10)

        self.main_window_frames.control.pack(side=Tk.LEFT, padx=10, pady=10)
        self.main_window_frames.application.pack(side=Tk.RIGHT, padx=10, pady=10)
        self.main_window_frames.plot_select.pack()
        self.main_window_frames.data_controls.pack()
    
    def reset_and_show_progress_bar(self, text):
        """
        Creates a new progress bar
        Args:
        text: Text to show
        """

        self.add_new_window("Progress Bar", (5, 0.5), False, False)

        self.progress_bar = TkProgressBarHelper(
            self.tk_handles.windows["Progress Bar"],
            {"text":text},
            {},
            orient="horizontal", length="5i", mode="determinate"
            )

        self.progress_bar.pack()

    def set_progress_text(self, text):
        """
        Sets the progress bar text
        Args:
        text: New text
        """
        self.progress_bar.set_label(text)
        
    def set_progress_percent(self, percent):
        """
        Updates the progress bar with a new percentage
        Args:
        pc: Percent to set the progress bar
        """

        self.progress_bar.set(percent)

    def hide_progress_bar(self):
        """
        Hides the progress bar
        """
        self.kill_window("Progress Bar")

    def kill_window(self, window):
        """
        Kills a Tk window`
        Args:
        window: The window to kill
        """
        try:
            self.tk_handles.windows[window].destroy()
        except KeyError:
            pass

    def add_new_window(self, key, size, add_figure=True, add_nav_toolbar=True):
        """
        Adds a new Tk window, overwriting if the key already exists
        Args:
        key: The name of the window
        size: (x, y) tuple of window size in inches
        add_figure: True if a matplotlib figure should be added to the window.
        add_nav_toolbar: True if a matplotlib toolbar should be added to the window.
        """
        window = self.root if key == "Main" else Tk.Toplevel(self.root)
        self.tk_handles.windows[key] = window
        self.tk_handles.frames[key] = Tk.Frame(window)
        if add_figure:
            self.tk_handles.figures[key] = Figure(figsize=size, dpi=100)

            self.tk_handles.canvases[key] = FigureCanvasTkAgg(
                self.tk_handles.figures[key], master=window)
            self.tk_handles.canvases[key].get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
            if add_nav_toolbar:
                self.tk_handles.toolbars[key] = NavigationToolbar2TkAgg(
                    self.tk_handles.canvases[key], window)
                self.tk_handles.toolbars[key].update()

    def get_figure(self, key):
        """
        Returns a handle to the requested figure (None if key does not exist)
        Args:
        key: The name of the window to get the handle for
        """
        try:
            return self.tk_handles.figures[key]
        except KeyError:
            return None

    def set_displayed_field(self, display_name, index):
        """
        For a particular subplot, change the displayed dataset.
        Args:
        display_name: The new name of the dataset
        index: The subplot for the dataset
        """
        get_module_logger().info("Setting subplot %d to %s", index, display_name)
        self.dataset_controls.set_subplot_display_name(index, display_name)

    def get_selected_dataset_name(self):
        """ Returns the currently selected dataset name (for selecting averaging) """
        return self.dataset_controls.get_dataset_name()

    def get_averaging_time_period(self):
        """ Returns the averaging time period from the text entry """
        return self.dataset_controls.get_averaging_time_period()

    def get_averaging_time_units(self):
        """ Returns the selected averaging period (seconds, minutes etc.) """
        return self.dataset_controls.get_averaging_time_units()

    def get_special_action(self):
        """ Returns the current selected special action """
        return self.dataset_controls.get_special_action()

    def set_dataset_choices(self, datasets):
        """ Sets the list of possible datasets that can be selected for each plot
        Args:
        datasets: List of datasets
        """

        get_module_logger().info("Setting dataset choices %s", ','.join(datasets))

        # When datasets are set, the full UI can be drawn
        self._draw_full_ui()

        self.dataset_controls.refresh_subplot_lists(datasets)

    def change_dataset_selection(self, selection):
        """ When a dataset is selected, shows or hides the special options picker
        Args:
        selection: The name of the dataset selected
        """
        special_options_list = self.application_request(REQS.GET_SPECIAL_ACTIONS, selection)
        self.dataset_controls.set_special_options(special_options_list, side=Tk.LEFT, padx=2)

    def _draw_full_ui(self):
        """
        Draws the full UI on the main figure (including dataset options
        """

        if self.ui_exists:
            return # No need to draw if already drawn!

        # Signal that the UI is drawn
        self.ui_exists = True

        self.dataset_controls.pack(side=Tk.LEFT, padx=2, pady=2)

        for frame in self.main_window_frames.data_controls_subframes:
            frame.pack(side=Tk.TOP, padx=3, pady=3)

        self.dataset_controls.pack_subplot_controls(side=Tk.LEFT)

    def get_index_of_displayed_plot(self, display_name):
        """
        Returns the subplot index (0 to 2) of a plot (or None if name is not displayed)
        Args:
        display_name: The requested display name
        """
        return self.dataset_controls.get_subplot_index_for_dataset(display_name)

    def draw(self, plotter, figure_key='Main'):
        """ Draw the a plot on a figure
        Args:
        plotter: The plotter object that will do the drawing
        figure_key: The key of the figure on which to plot
        """
        current_subplots = self.dataset_controls.get_subplot_list()
        styles = [
            self.application_request(REQS.GET_PLOTTING_STYLE, display_name) for display_name in current_subplots
        ]
        
        plotter.draw(self.tk_handles.figures[figure_key], styles)
        self.tk_handles.canvases[figure_key].draw()

    def _exit(self):
        """
        Exits the application by quitting the Tk loop
        """
        if messagebox.askyesno(app_info.TITLE, "Exit %s?" % app_info.TITLE):
            self.root.quit()
            if os.name == "nt":
                # this is necessary on Windows to prevent "Fatal Python Error: PyEval_RestoreThread: NULL tstate"
                self.root.destroy()
