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

def load_global_config(path):
    global_config = configparser.RawConfigParser()
    global_config.read_file(codecs.open(path+"/config.ini", "r", "utf8"))
    
def load_dataset_config(directory):
    full_path = directory+"/config.txt"
    if os.path.exists(full_path):
        get_module_logger().info("Reading config from %s", full_path)
        dataset_config = configparser.RawConfigParser()
        dataset_config.optionxform = str # Makes parser case sensitive
        dataset_config.read_file(codecs.open(full_path, "r", "utf8"))
    else:
        get_module_logger().info("No config from %s", full_path)
        dataset_config = None

def get_dataset_config(section, key=None):
    
    if key is not None:
        return section[key]
    else:
        return dataset_config[section]

def get_units():
    units = dict(self.global_config['UNITS'])
    if 'UNITS' in self.dataset_config.keys():
            # Merge units into the global configuration
            units = dict(units + dict(self.dataset_config['UNITS']))

def has_dataset_config():
    return dataset_config is not None