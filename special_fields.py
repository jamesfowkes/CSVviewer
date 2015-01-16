"""
special_fields.py

@author: James Fowkes

Classes to perform special modifications to data
"""

import pandas as pd
import numpy as np
import abc

def get_special_field(type, field_name, display_name, args=None):
    if type == "WS":
        #args[0] should be the calibration factor for the windspeed
        return Windspeed(field_name, display_name, args[0] if args else None)
    elif type == "HUM":
        return Humidity(field_name, display_name)
    elif type == "WD":
        return WindDirection(field_name, display_name)
    elif type == "Flush Seconds":
        return FlushSeconds(field_name, display_name)
        
class SpecialField(object):

    """
    Base class ("interface") for a special field
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, field_name, display_name):
        """
        Args:
        field_name : The name the field has in the CSV file
        display_name : The name the field should have in plots/GUIs
        """
        self.field_name = field_name
        self.display_name = display_name

    @abc.abstractmethod
    def convert(self, dataframe):
        """
        Converts data and timestamps as required
        To be overridden by subclasses
        """
        return
    
    @abc.abstractmethod
    def capabilities(self, manager):
        """
        Returns list of additional capabilities (e.g. a histogram plot)
        To be overridden by subclasses
        Args:
        manager: Data manager (to query the existence of other datasets,
            for example windrose plot is only an option if both speed and direcion exist)
        """

        return None

class Humidity(SpecialField):

    """ Humidity data is stored as decimal between 0.0 and 1.0.
    It should be displayed as 0% to 100% """

    def __init__(self, field_name, display_name):
        """
        Args:
        field_name : The fieldname of the humidity field
        display_name : The name the field should have in plots/GUIs
        """
        SpecialField.__init__(self, field_name, display_name)

    def convert(self, dataframe):

        """
        Humidity comes in as decimal from 0 to 1.0. Convert to 0 to 100%
        Args:
        dataframe : The data to convert
        """
        new_dataframe = dataframe * 100

        return new_dataframe


    def capabilities(self, _):
        """ Humidity has no special capabilities
        Args:
        _:Placeholder for data manager (not used)
        """
        return None

class Windspeed(SpecialField):

    """ Windspeed data is stored as number of pulses between two timestamps.
    This needs to be converted to a speed in meters per second by:
    1. Convert pulses-per-timestamp into pulses-per-second
    2. Convert pulses-per-second into meters per second by applying a fixed calibration factor
    """

    def __init__(self, field_name, display_name, calibration_factor):
        """
        Args:
        field_name: The fieldname of the humidity field
        display_name : The name the field should have in plots/GUIs
        calibration_factor : The number to multiply each data point by to get m/s
        """
        self.factor = float(calibration_factor) if calibration_factor is not None else 200 #Default calibration factor
        SpecialField.__init__(self, field_name, display_name)

    def convert(self, dataframe):

        """
        Conversion to m/s speed is a two stage process:
        1. Calculate pulses-per-second between two timestamps
            e.g. Between 10:00:00 and 10:00:30 there were 74 pulses.
            This is 74/30 = 2.47 pulses per second.
            This is represented as a SINGLE data point at time 10:00:15.
        2. For each of the new datapoints, convert pulses-per-second to meters-per-second by applying calibration factor
            e.g. With a factor of 0.7, 2.47 * 0.7 = 1.727 m/s

        Note that this conversion discards the FIRST datapoint from pulses data.
        This is done because there is no way to determine how the time period over which
        the pulse data was gathered

        Args:
        dataframe : The dataframe to convert
        """

        # Convert timestamps to time deltas
        # pylint's underlying astroid library cannot find numpy functions
        # So disable then re-enable warning.
        # http://stackoverflow.com/questions/20553551/how-do-i-get-pylint-to-recognize-numpy-members
        # This suggests that another astroid version can do this, so check in the future.
        #pylint: disable=no-member
        diffs = np.diff(dataframe.index)
        deltas_seconds = diffs/np.timedelta64(1, 's')
        #pylint: enable=no-member
        # Use deltas to calculate windspeed
        windspeed = list(dataframe[self.field_name].values)

        # Apply the constant calibration factor
        windspeed = [pulses * self.factor for pulses in windspeed[1:]]

        # Divide by the delta to get m/s
        speeds = [speed/delta for speed, delta in zip(windspeed, list(deltas_seconds))]

        # Need to re-index these data to time points in middle of timestamps
        old_timestamps = list(dataframe.index.values)[:-1]
        new_timestamps = old_timestamps + (diffs / 2)
        return pd.DataFrame({self.field_name:speeds}, index=new_timestamps)

    def capabilities(self, manager):
        """ Returns a list of the special functions that can be performed with this dataset """

        caps = ["Histogram"] # Can always do histogram with this data

        if manager.has_dataset("Direction") and manager.len("Direction") == manager.len("Wind Speed"):
            caps.append("Windrose")

        return caps

class WindDirection(SpecialField):
    """
    Wind direction data is assumed to come as cardinal points (N, E, S, W etc).
    Conversion is performed to degrees (0 to 359)
    """
    def __init__(self,  field_name, display_name):
        """
        Args:
        field_name: The fieldname of the direction field
        display_name : The name the field should have in plots/GUIs
        """
        SpecialField.__init__(self, field_name, display_name)

    def convert(self, dataframe):
        """
        Maps cardinal compass directions to degrees
        Args:
        dataframe : The dataframe to convert
        """

        # Map cardinal points to degrees (replaced with "not a number" 'D' entry)

        # pylint's underlying astroid library cannot find numpy functions
        # So disable then re-enable warning.
        # http://stackoverflow.com/questions/20553551/how-do-i-get-pylint-to-recognize-numpy-members
        # This suggests that another astroid version can do this, so check in the future.
        #pylint: disable=no-member
        cardinal_to_deg_map = {'N':0, 'NE':45, 'E':90, 'SE':135, 'S':180, 'SW':225, 'W':270, 'NW':315, 'D':np.nan}
        #pylint: enable=no-member
        dataframe = dataframe.replace({'Direction':cardinal_to_deg_map})

        # Drop first point (since this data will be plotted against windspeed which drops first point also)
        dataframe = dataframe.ix[1:]

        # Drop any NaNs
        dataframe = dataframe.dropna()

        return dataframe

    def capabilities(self, _):
        """ Wind direction has no special capabilities
        Args:
        _:Placeholder for data manager (not used)
        """
        return None
        
class FlushSeconds(SpecialField):

    """
    Flush duration data is only special because it can be histogram'd
    """

    def __init__(self,  field_name, display_name):
        """
        Args:
        field_name: The fieldname of the flush seconds field
        """
        SpecialField.__init__(self,  field_name, display_name)
        
    def convert(self, dataframe):

        """
        No conversion is required for this dataset
        Args:
        dataframe : The dataframe to convert
        """

        return dataframe
        
    def capabilities(self, manager):
        
        """ Returns a list of the special functions that can be performed with this dataset """
        return ["Histogram"]
