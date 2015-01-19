"""
application.py

@author: James Fowkes

Entry file for the CSV viewer application
"""

import argparse
import logging
import codecs
import os

import configmanager

from datamanager import DataManager, EVT_DATA_LOAD_COMPLETE, EVT_DATA_PROCESSING_COMPLETE
from gui import GUI, ask_directory, run_gui, show_info_dialog
from plotter import Plotter, WindPlotter, Histogram
from app_reqs import REQS

import queue
import threading

from app_info import VERSION, TITLE

def get_arg_parser():
    """ Return a command line argument parser for this module """
    arg_parser = argparse.ArgumentParser(
        description='Datalogger CSV Viewer')

    arg_parser.add_argument(
        '--start_folder', dest='start_folder', default=None,
        help="The folder to look for CSVs in")

    return arg_parser

def get_module_logger():

    """ Returns logger for this module """
    return logging.getLogger(__name__)

#pylint: disable=too-many-instance-attributes
# Accept this warning, as application is not likely to grow
# beyond current # of attributes on the short term. Refactoring
# is likely to cause more confusion.
# Consider refactoring if application grows significantly.

class Application:

    """
    Handles interaction between GUI events, GUI drawing, plotting, file reading etc.
    """

    def __init__(self, _):

        """
        Args:
        _ : Command line arguments (not currently used)
        """

        self.plotter = Plotter()
        self.windplotter = WindPlotter()
        self.histogram = Histogram()

        self.msg_queue = None
        self.loading_timer = None
        self.data_manager = None

        self.gui = GUI(self.request_handler)

    def action_about_dialog(self): # pylint: disable=no-self-use
        """
        Show information about this program
        pylint warning no-self-use is disabled. While this function
        makes no use of self, it needs to be part of the application object
        as it gets used by the GUI
        """
        info = """
        %s
        Version %s

        Created by:
        Matt Little
        James Fowkes

        http://www.re-innovation.co.uk
        Nottingham, UK

        windrose code adapted from
        http://sourceforge.net/projects/windrose/files/windrose/
        by joshua_fr
        """ % (TITLE, VERSION)

        show_info_dialog(info)

    def request_handler(self, request, *args):
        if request == REQS.CHANGE_SUBPLOT1:
            self.action_subplot_change(0, args[0])
        elif request == REQS.CHANGE_SUBPLOT2:
            self.action_subplot_change(1, args[0])
        elif request == REQS.CHANGE_SUBPLOT3:
            self.action_subplot_change(2, args[0])
        elif request == REQS.AVERAGE_SUBPLOT_DATA:
            self.action_average_data()
        elif request == REQS.RESET_SUBPLOT_DATA:
            self.action_reset_average_data()
        elif request == REQS.SPECIAL_ACTION:
            self.action_special_action()
        elif request == REQS.NEW_DATA:
            self.action_new_data()
        elif request == REQS.ABOUT_DIALOG:
            self.action_about_dialog()
        elif request == REQS.GET_SPECIAL_ACTIONS:
            return self.data_manager.get_special_dataset_options(args[0])
        elif request == REQS.GET_PLOTTING_STYLE:
            return self.get_plotting_style_for_field(args[0])

    def action_subplot_change(self, subplot_index, display_name):

        """ Handles request to change subplot data
        Args:
        subplot_index : The index of the subpolot (0 to 2) to change
        display_name : The display name of the requested data series
        """

        get_module_logger().info("Changing subplot %d to %s", subplot_index, display_name)

        self.plotter.set_visibility(subplot_index, display_name != "None")
        self.gui.set_displayed_field(display_name, subplot_index)

        self.gui.set_dataset_choices(self.data_manager.get_numeric_display_names())

        if display_name != "None":
            self.plotter.set_dataset(
                self.data_manager.get_timestamps(display_name), self.data_manager.get_dataset(display_name),
                display_name, subplot_index)

        self.gui.draw(self.plotter)

    def action_average_data(self):

        """ Handles request to show the average of a dataset """

        # Get the dataset of interest
        display_name = self.gui.get_selected_dataset_name()

        # Get the time period over which to average
        try:
            time_period = self.gui.get_averaging_time_period()
        except ValueError:
            return # Could not convert time period to float

        if time_period == 0:
            return # Cannot average over zero time!

        # Get the units the time period is in (seconds, minutes etc.)
        time_units = self.gui.get_averaging_time_units()

        get_module_logger().info("Averaging %s over %d %s", display_name, time_period, time_units.lower())

        time_multipliers = {"Seconds":1, "Minutes":60, "Hours":60*60, "Days":24*60*60, "Weeks":7*24*60*60}

        time_period_seconds = time_period * time_multipliers[time_units]

        (data, timestamps) = self.data_manager.get_dataset_average(display_name, time_period_seconds)

        index = self.gui.get_index_of_displayed_plot(display_name)

        self.plotter.set_dataset(timestamps, data, display_name, index)

        self.gui.draw(self.plotter)

    def get_plotting_style_for_field(self, display_name):
        
        styles = None
        if configmanager.has_dataset_config() and display_name is not None:
            try:
                field_name = self.data_manager.get_field_name_from_display_name(display_name)
                styles = configmanager.get_dataset_config('FORMATTING', field_name)

                styles = [style.strip() for style in styles.split(",")]

                if styles[0] == '':
                    styles[0] = 'line' #Add the default plot style
    
                if len(styles) == 1:
                    styles.append('b') #Add the default colour (blue)

            except KeyError:
                pass # This field name not in the config file
        
        return ["line","b"] if styles is None else styles
        
    def action_reset_average_data(self):

        """ Get the dataset of interest and reset the original data """

        display_name = self.gui.get_selected_dataset_name()
        subplot_index = self.gui.get_index_of_displayed_plot(display_name)

        get_module_logger().info("Resetting dataset %s on subplot %d", display_name, subplot_index)

        self.plotter.set_dataset(
            self.data_manager.get_timestamps(display_name), self.data_manager.get_dataset(display_name),
            display_name, subplot_index)

        self.gui.draw(self.plotter)
        
    def action_new_data(self):

        """ Handles request to show open a new set of CSV files """

        new_directory = ask_directory("Choose directory to process")

        if new_directory != '' and DataManager.directory_has_data_files(new_directory):
            get_module_logger().info("Parsing directory %s", new_directory)
            
            configmanager.load_dataset_config(new_directory)

            self.gui.reset_and_show_progress_bar("Loading from folder '%s'" % new_directory)

            self.msg_queue = queue.Queue()
            self.data_manager = DataManager(self.msg_queue, new_directory)
            self.data_manager.start()

            self.loading_timer = threading.Timer(0.1, self.check_data_manager_status)
            self.loading_timer.start()

    def check_data_manager_status(self):

        """ When the data manager is loading new data, updates the progress bar """

        dataloader_finished = False
        try:
            msg = self.msg_queue.get(0)
            if msg == EVT_DATA_LOAD_COMPLETE:
                self.gui.set_progress_text("Processing data...")
                self.gui.set_progress_percent(0)
            elif msg == EVT_DATA_PROCESSING_COMPLETE:
                # Data has finished loading.
                dataloader_finished = True
                self.gui.hide_progress_bar()
                self.plot_datasets()
            else:
                self.gui.set_progress_percent(msg)
        except queue.Empty:
            pass
        except:
            raise

        if not dataloader_finished:
            self.loading_timer = threading.Timer(0.1, self.check_data_manager_status)
            self.loading_timer.start()

    def action_special_option(self):

        """ Handles requests for special options
        e.g. histogram, windrose plot """

        action = self.gui.get_special_action()

        if action == "Windrose":

            get_module_logger().info("Plotting windrose")
            self.gui.add_new_window('Windrose', (7, 6))

            # Get the wind direction and speed data
            speed = self.data_manager.get_dataset('Wind Speed')
            direction = self.data_manager.get_dataset('Direction')

            self.windplotter.set_data(speed, direction)

            # Add window and axes to the GUI
            try:
                self.gui.draw(self.windplotter, 'Windrose')
            except Exception as exc: #pylint: disable=broad-except
                get_module_logger().info("Could not plot windrose (%s)", exc)
                show_info_dialog(
                    "Could not plot windrose - check that the windspeed and direction data are valid")

        elif action == "Histogram":
            get_module_logger().info("Plotting histogram")
            self.gui.add_new_window('Histogram', (7, 6))

            # Get the data for the histogram
            dataset_name = self.gui.get_selected_dataset_name()
            speed = self.data_manager.get_dataset(dataset_name)

            self.histogram.set_data(speed, dataset_name)

            # Add window and axes to the GUI
            self.gui.draw(self.histogram, 'Histogram')

    def plot_datasets(self):

        """ Plots the default set of data (from configuration file) """

        self.plotter.clear_data()

        # Get the default fields from config
        default_fields = configmanager.get_global_config('DEFAULT', 'DefaultFields')
        default_fields = [field.strip() for field in default_fields.split(",")]

        # Drawing mutiple plots, so turn off drawing until all three are processed
        self.plotter.suspend_draw(True)

        field_count = 0
        numeric_fields = self.data_manager.get_numeric_field_names()
        for field in default_fields:
            if field in numeric_fields:
                display_name = self.data_manager.get_display_name(field)
                self.action_subplot_change(field_count, display_name)
                field_count += 1
        
        # If field count is less than 3, fill the rest of the plots in order from datasets
        for field in numeric_fields:
            if field_count == 3:
                break # No more fields to add
            
            if field in default_fields:
                continue # Already added, move onto next field
            
            display_name = self.data_manager.get_display_name(field)
            self.action_subplot_change(field_count, display_name)
            field_count += 1
            
        # Now the plots can be drawn
        self.gui.set_dataset_choices(self.data_manager.get_numeric_display_names())
        self.plotter.suspend_draw(False)
        self.gui.draw(self.plotter)

def main():

    """ Application start """

    logging.basicConfig(level=logging.INFO)

    get_module_logger().setLevel(logging.INFO)

    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    configmanager.load_global_config(".")
    
    # The call to run() does not return.
    # All events are handled via GUI handlers and application callbacks.

    _ = Application(args)

    run_gui()

if __name__ == "__main__":
    main()

