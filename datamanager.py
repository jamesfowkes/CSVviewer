"""
datamanager.py

@author: James Fowkes

Datamanager class for data from CSV files
"""

import pandas as pd
import os
import logging

import threading

from datetime import timedelta

import configmanager

from special_fields import get_special_field

# Data loading events
EVT_DATA_LOAD_COMPLETE = -1
EVT_DATA_PROCESSING_COMPLETE = -2

def valid_filename(filename):
    """ Returns true if the filename ends with .csv.
    Used for filtering a directory listing for valid files """
    return filename.lower().endswith(".csv")

def get_module_logger():

    """ Returns logger for this module """
    return logging.getLogger(__name__)

def get_csv_filenames(folder):

    """ Get a list of valid CSV files
    Args:
    folder: folder to search in
    """

    filenames = []
    for filename in os.listdir(folder):
        if valid_filename(filename):
            filenames.append(filename)

    return filenames

class DataManager(threading.Thread):

    """
    The data manager is responsible for reading CSV files, performing data
    conversions and presenting dataframes to the application.

    The data manager is dependent on the pandas library for dataset processing.

    The data manager runs in a separate thread to the rest of the application.
    This is so the application can get IO status updates during long operations
    such as CSV file read and parsing.
    """
    def __init__(self, msg_queue, folder):
        threading.Thread.__init__(self)
        self.queue = msg_queue
        self.folder = folder

        self._numeric_fields = None
        self._display_to_field_dict = None
        self._field_to_display_dict = None
        self.dataframes = None

        # These fields have special processing applied before they are displayed
        self.special_fields = {}
        try:
            for field_name, field_options in configmanager.get_dataset_config('SPECIAL FIELDS').items():
                # Each field_options is a comma-separated list of options
                field_options = [option.strip() for option in field_options.split(",")]
                field_type = field_options[0] # The first option is the type of field
                display_name = field_options[1] # The first option is the name to use for display
                other_args = field_options[2:] #Any additional arguments for this field
                self.special_fields[field_name] = get_special_field(field_type, field_name, display_name, other_args)
        except KeyError:
            pass # No special fields named in config file
        
        # Some fields might want to be limited by the user
        self.limits = {}
        try:
            for display_name, limits in configmanager.get_dataset_config('LIMITS').items():
                #limits should be two numbers separated by a comma
                try:
                    limits = limits.split(",")
                    if len(limits) == 2:
                        self.limits[display_name] = [float(limits[0]), float(limits[1])]
                except ValueError:
                    pass # Could not convert limits: just leave as no limits
        except KeyError:
            pass # No limits specified in config file
        
    def run(self):
        """
        Parse the file with pandas
        Use columns 1 and 2 to get datetime from
        This creates a new column 0, which is the combined datetime used as index
        """

        filenames = get_csv_filenames(self.folder)

        frames = []
        total_file_count = len(filenames)
        percent_complete = 0

        for fcount, filename in enumerate(filenames):

            # Create a dataframe for each CSV file and append to the frames list

            full_path = os.path.join(self.folder, filename)
            dataframe = pd.read_csv(full_path, parse_dates=[[1, 2]], dayfirst=True, index_col=0)
            frames.append(dataframe)

            percent_complete = (fcount * 100) / total_file_count
            self.queue.put(percent_complete)

        self.queue.put(EVT_DATA_LOAD_COMPLETE)
        
        # All dataframes created, now merge them and sort by time
        data = pd.concat(frames)
        data.sort_index(inplace=True)

        self.queue.put(20)

        # Strip any whitespace from the column names
        data.rename(columns=lambda x: x.strip(), inplace=True)

        self.queue.put(40)

        # Split data into seperate dataframes (ignoring reference field)
        column_names = list(data.columns.values)[1:]
        self.dataframes = {}
        for col in column_names:
            self.dataframes[col] = pd.DataFrame(data[col], index=data.index)

        self.queue.put(60)

        # Apply any special data conversions
        for key, dataframe in self.dataframes.items():
            try:
                self.dataframes[key] = self.special_fields[key].convert(dataframe)
                get_module_logger().info("Applied special conversion to field '%s'", key)
            except KeyError:
                get_module_logger().info("No special conversion exists for field '%s'", key)
                pass # No special field exists for this data
            except:
                raise
                
        self.queue.put(80)

        # The fields are fixed, so save them to a member now rather than compute each time
        self._set_fieldnames(column_names)

        # Can also get numeric fieldnames now
        self._set_numeric_fields()

        # Apply any user-specified limits
        for key, limit in self.limits.items():
            get_module_logger().info("Applying limits (%d, %d) to field %s",
                limit[0], limit[1], key)
                
            field_name = self._display_to_field_dict[key]
            
            df = self.dataframes[key]
            
            max_limit = limit[1]
            self.dataframes[key] = self.dataframes[key][self.dataframes[key][key] <= max_limit]
            
            min_limit = limit[0]
            self.dataframes[key] = self.dataframes[key][self.dataframes[key][key] >= min_limit]
                        
        # Signal to main thread that data load and conversion is complete
        self.queue.put(100)
        self.queue.put(EVT_DATA_PROCESSING_COMPLETE)

    def _set_fieldnames(self, names):
        """
        Get a set of display names from field names
        """

        self._field_to_display_dict = {}
        self._display_to_field_dict = {}
        for name in names:
            try:
                display_name = self.special_fields[name].display_name
                self._field_to_display_dict[name] = display_name
                self._display_to_field_dict[display_name] = name
            except KeyError: # Special field does not exist for this field
                self._field_to_display_dict[name] = name
                self._display_to_field_dict[name] = name

    def _set_numeric_fields(self):
        """ Set field names of fields that can be considered numeric data """

        # Datatype can be considered numeric if its kind is one of b,i,u,f,c
        # These are numpy kinds (see http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html)
        # (boolean, integer, unsigned, float, complex)

        frames = [dataframe for (key, dataframe) in self.dataframes.items() if dataframe[key].dtype.kind in 'biufc']

        self._numeric_fields = [list(frame.columns.values)[0] for frame in frames]

    def get_timestamps(self, display_name):
        """ Return timestamps (the dataframe index) for the requested series """
        field_name = self._display_to_field_dict[display_name]
        return self.dataframes[field_name].index

    def has_dataset(self, display_name):
        """ Return true if dataset with this name exists in datasets """
        return display_name in self._display_to_field_dict.keys()

    def get_dataset(self, display_name):
        """ Return data for the requested series """
        field_name = self._display_to_field_dict[display_name]
        return self.dataframes[field_name][field_name].values

    def get_dataset_average(self, display_name, average_time_seconds):
        """ Use resampling functionality to get average of dataset over requested number of seconds """
        field_name = self._display_to_field_dict[display_name]
        resampled_data = self.dataframes[field_name].resample("%dS" % average_time_seconds, how='mean')
        # Resampled data is placed at start of time periods. Re-index to middle of periods.
        new_index = resampled_data.index + timedelta(seconds=average_time_seconds/2)
        resampled_data.index = new_index

        return (list(resampled_data[field_name].values), list(resampled_data[field_name].index))

    def len(self, display_name):
        """ Returns length of a dataframe
        Returns 0 if the requested frame does not exist
        Args:
        display_name : the dataframe to get length of
        """
        try:
            field_name = self._display_to_field_dict[display_name]
            return len(self.dataframes[field_name][field_name])
        except KeyError:
            return 0

    def _get_all_display_names(self):
        """ Returns a list of display names from the dictionary """
        return list(self._field_to_display_dict.values())

    def get_special_dataset_options(self, dataset):
        """ Returns a list of special capabilities for a dataset.
        For example a windspeed dataset can also be displayed as a histogram.
        See specialfield.py for more information
        Args:
        dataset: the dataset of interest
        """
        field_name = self._display_to_field_dict[dataset]
        try:
            special_field = self.special_fields[field_name]
            return special_field.capabilities(self)
        except KeyError: # Field does not exist, so no capabilities
            return None
        except:
            raise

    def get_numeric_display_names(self):
        """ Return display names of fields that can be considered numeric data """
        return [self._field_to_display_dict[key] for key in self._numeric_fields]

    def get_numeric_field_names(self):
        """ Return display names of fields that can be considered numeric data """
        return self._numeric_fields.copy()

    def get_field_name_from_display_name(self, display_name): #pylint: disable=invalid-name
        """ For a given "nice" display name from special field return the field name (from CSV file) """
        return self._display_to_field_dict[display_name]

    def get_display_name(self, field_name):
        """ Returns the display name associated with a field name """
        return self._field_to_display_dict[field_name]

    @staticmethod
    def directory_has_data_files(directory):
        """ Returns True if directory has at least one .csv or .CSV file """
        return True in [".csv" in filename.lower() for filename in os.listdir(directory)]
