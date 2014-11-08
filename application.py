"""
application.py

@author: James Fowkes

Entry file for the CSV viewer application
"""

import sys
import argparse
import logging
import configparser
import codecs

from csv_parser import CSV_Parser
from csv_gui import CSV_GUI
from csv_plotter import CSV_Plotter

from menu import Menu, MenuOption

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
       
class Application:
    
    def __init__(self, args, config):
        
        self.parser = CSV_Parser(None)
        
        self.config = config
        
        self.plotter = CSV_Plotter(config)
        self.gui = CSV_GUI(self)
    
    def action_print_summary(self, menu_level):
        print("Current directory: %s" % self.parser.folder)
        print("Found %d valid .csv files" % self.parser.file_count)
        print("Total records: %d" % self.parser.record_count)
        print("Data fields:")
        for field in self.parser.fields:
            print("\t" + field)
    
    def action_subplot1_change(self, dataset_choice):
        """ Pass though to action_subplot_change """
        self.action_subplot_change(0, dataset_choice)
        
    def action_subplot2_change(self, dataset_choice):
        """ Pass though to action_subplot_change """
        self.action_subplot_change(1, dataset_choice)
        
    def action_subplot3_change(self, dataset_choice):
        """ Pass though to action_subplot_change """
        self.action_subplot_change(2, dataset_choice)
    
    def action_subplot_change(self, subplot_index, display_name):

        if display_name == "None":
            self.plotter.set_visibility(subplot_index, False)
            self.gui.set_displayed_field(display_name, subplot_index)
            self.gui.set_dataset_choices(self.parser.get_numeric_fields())
        else:
            field_name = self.parser.get_field_name_from_display_name(display_name)
            self.plotter.set_visibility(subplot_index, True)
            self.gui.set_displayed_field(display_name, subplot_index)
            self.gui.set_dataset_choices(self.parser.get_numeric_fields())
            self.plotter.set_dataset(self.parser.get_timestamps(field_name), self.parser.get_dataset(field_name), display_name, subplot_index)
        
        self.gui.draw(self.plotter)
            
    def action_average_data(self):
        # Get the dataset of interest and convert display name to field name
        display_name = self.gui.get_averaging_displayname()       

        try:
            field_name = self.parser.get_field_name_from_display_name(display_name)
        except IndexError:
            return # Display name does not exist  

        # Get the time period over which to average
        try:
            time_period = self.gui.get_averaging_time_period()
        except ValueError:
            return # Could not convert time period to float
        
        if time_period == 0:
            return # Cannot average over zero time!

        # Get the units the time period is in (seconds, minutes etc.)
        time_units = self.gui.get_averaging_time_units()

        print("Averaging %s over %d %s" % (field_name, time_period, time_units.lower()))
       
            
    def action_new_data(self):
        
        new_directory = self.gui.ask_directory("Choose directory to process")
        
        if new_directory != '' and self.parser.directory_has_data_files(new_directory):
            self.parser.parse(new_directory)
            self.plot_default_datasets()
            
    def run(self):
        self.gui.run()
       
    def plot_default_datasets(self):
        
        self.plotter.clear_data()
        
        # Get the default fields from config
        default_fields = self.config['DEFAULT']['DefaultFields']
        default_fields = [field.strip() for field in default_fields.split(",")]

        # Drawing mutiple plots, so turn off drawing until all three are processed
        self.plotter.suspend_draw(True)
        
        field_count = 0
        for field in default_fields:
            if field in self.parser.get_fields():
                display_name = self.parser.get_display_name(field)
                
                self.action_subplot_change(field_count, display_name)
                field_count += 1
        
        # Now the plots can be drawn
        self.plotter.suspend_draw(False)
        
        self.gui.set_dataset_choices(self.parser.get_numeric_fields())
        self.gui.draw(self.plotter)
        
def main():

    """ Application start """

    logging.basicConfig(level=logging.INFO)

    get_module_logger().setLevel(logging.INFO)

    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()
    
    conf_parser = configparser.RawConfigParser()
    conf_parser.read_file(codecs.open("config.ini", "r", "utf8"))
            
    app = Application(args, conf_parser)
    
    app.run()
    
if __name__ == "__main__":
    main()
