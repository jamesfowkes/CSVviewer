"""
configmanager.py

@author: James Fowkes

Configuration manager for the CSV viewer application
"""

import configparser
import codecs
import os
import logging

global_config = None
dataset_config = None

def get_module_logger():

    """ Returns logger for this module """
    return logging.getLogger(__name__)

def load_global_config(directory):
    global global_config

    full_path = directory+"/config.ini"

    if os.path.exists(full_path):
        global_config = configparser.RawConfigParser()
        get_module_logger().info("Reading global config from %s", full_path)
        global_config.read_file(codecs.open(full_path, "r", "utf8"))
    else:
        get_module_logger().info("No config from %s", full_path)
        global_config = {}

def load_dataset_config(directory):
    global dataset_config
    full_path = directory+"/config.txt"
    if os.path.exists(full_path):
        get_module_logger().info("Reading dataset config from %s", full_path)
        dataset_config = configparser.RawConfigParser()
        dataset_config.optionxform = str # Makes parser case sensitive
        dataset_config.read_file(codecs.open(full_path, "r", "utf8"))
    else:
        get_module_logger().info("No config from %s", full_path)
        dataset_config = {}

def get_global_config(section, key=None):
    """ Returns a section or a value from the loaded global configuration
    Args:
    section : The section to search
    key : The key to look for
    """
    global global_config

    if key is not None:
        # Return the requested value from the section
        try:
            return global_config[section][key]
        except KeyError:
            return "" # If value does not exist, return an empty string
    else:
        # Return the whole requested section as a dict
        try:
            return dict(global_config[section])
        except KeyError:
            return {} # If section does not exist, return an empty dict

def get_dataset_config(section, key=None):
    """ Returns a section or a value from the loaded dataset configuration
    Args:
    section : The section to search
    key : The key to look for
    """

    global dataset_config

    if key is not None:
        # Return the requested value from the section
        try:
            return dataset_config[section][key]
        except KeyError:
            return "" # If value does not exist, return an empty string
    else:
        # Return the whole requested section as a dict
        try:
            return dict(dataset_config[section])
        except KeyError:
            return {} # If section does not exist, return an empty dict

def get_units():
    global global_config
    global dataset_config

    global_units = list(dict(global_config['UNITS']).items())
    if 'UNITS' in dataset_config.keys():
            # Merge units into the global configuration
            dataset_units = list(dict(dataset_config['UNITS']).items())
            units = dict(global_units + dataset_units)
    else:
        units = dict(global_units)

    return units

def has_dataset_config():
    global dataset_config
    return dataset_config is not None
