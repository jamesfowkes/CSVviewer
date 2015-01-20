"""
configmanager.py

@author: James Fowkes

Configuration manager for the CSV viewer application
"""

import configparser
import codecs
import os
import logging

def get_module_logger():

    """ Returns logger for this module """
    return logging.getLogger(__name__)

def load_config(full_path):
    """ Loads a configuration object from given path """
    if os.path.exists(full_path):
        config = configparser.RawConfigParser()
        config.optionxform = str # Makes parser case sensitive
        config.read_file(codecs.open(full_path, "r", "utf8"))
    else:
        get_module_logger().info("No config from %s", full_path)
        config = {}

    return config

class ConfigManager:

    """
    A class to handle reading a global config file (for the application)
    and a dataset config file (each time new data is loaded).

    It also handles returning that data to the application.
    """

    def __init__(self, global_dir=None):
        """
        The class is very simple.
        It has two members that hold the configuration objects
        """
        self.global_config = None
        self.dataset_config = None

        if global_dir is not None:
            self.load_global_config(global_dir)

    def load_global_config(self, directory):
        """ Loads the global configuration from the given directory """
        path = directory+"/config.ini"
        get_module_logger().info("Reading global config from %s", path)
        self.global_config = load_config(path)

    def load_dataset_config(self, directory):
        """ Loads a dataset configuration from the given directory """
        path = directory+"/config.txt"
        get_module_logger().info("Reading dataset config from %s", path)
        self.dataset_config = load_config(path)

    def get_global_config(self, section, key=None):
        """ Returns a section or a value from the loaded global configuration
        Args:
        section : The section to search
        key : The key to look for
        """

        if key is not None:
            # Return the requested value from the section
            try:
                return self.global_config[section][key]
            except KeyError:
                return "" # If value does not exist, return an empty string
        else:
            # Return the whole requested section as a dict
            try:
                return dict(self.global_config[section])
            except KeyError:
                return {} # If section does not exist, return an empty dict

    def get_dataset_config(self, section, key=None):
        """ Returns a section or a value from the loaded dataset configuration
        Args:
        section : The section to search
        key : The key to look for
        """

        if key is not None:
            # Return the requested value from the section
            try:
                return self.dataset_config[section][key]
            except KeyError:
                return "" # If value does not exist, return an empty string
        else:
            # Return the whole requested section as a dict
            try:
                return dict(self.dataset_config[section])
            except KeyError:
                return {} # If section does not exist, return an empty dict

    def get_units(self):
        """
        Returns a dictionary of units to use for fields,
        where the keys are fields and values are the unit strings to use
        """

        # First get the standard list from the global configuration
        # Get as a list of key, value tuples since it might be merged with the
        # dataset units.
        global_units = list(dict(self.global_config['UNITS']).items())

        if 'UNITS' in self.dataset_config.keys():
            # Merge the dataset units into the global configuration

            # Get the dataset units as a list of (key, value) tuples
            dataset_units = list(dict(self.dataset_config['UNITS']).items())

            # Merge with the dictionary list and convert to dict
            units = dict(global_units + dataset_units)
        else:
            # No dataset unit specified, so just turn the global back into a list
            units = dict(global_units)

        return units

    def has_dataset_config(self):
        """ Return true if a dataset config has been loaded """
        return self.dataset_config is not None

