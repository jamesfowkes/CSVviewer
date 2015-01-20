"""
csv_plotter.py

@author: James Fowkes

Defines a data plotter for the CSV viewer application using

"""

import logging

from windrose import WindroseAxes

def get_module_logger():
    """ Returns logger for this module """
    return logging.getLogger(__name__)

#pylint: disable=too-few-public-methods
class InvalidDataException(Exception):
    """ Just rename the base exception class """
    pass

class DataSet:

    """ Simple object to store data, timestamps and a label for the data """

    def __init__(self, ylabel, data, times):
        self.ylabel = ylabel
        self.data = data
        self.times = times

class WindPlotter:

    """ Implements a windrose plot """

    def __init__(self, configmanager):
        """ Initialise the wind plotter """
        self.windspeed = None
        self.direction = None
        self.configmanager = configmanager

    def set_data(self, speed, direction):
        """
        Args:
        speed - The speed data to display
        direction - The direction data to display
        len(speed) must equal len(direction)
        """

        if len(speed) == len(direction):
            self.windspeed = speed
            self.direction = direction
        else:
            raise InvalidDataException(
                "Length of direction (%d) and speed (%d) lists are not equal" % (len(direction), len(speed)))

    def draw(self, fig):

        """ Draw windrose plot of current data on figure """

        try:
            axes = WindroseAxes(fig, rect=[0.1, 0.1, 0.8, 0.8])
            fig.add_axes(axes)

            axes.bar(self.direction, self.windspeed, normed=True)

            axes.set_title("Windrose (by % in 6 bins)")
            legend = axes.legend(borderaxespad=-0.10, fontsize=8, bbox_to_anchor=(-0.2, 0))

            legend_title = "Wind Speed"

            try:
                #Try adding a unit to the legend title
                units = self.configmanager.get_units() # Get unit strings from config
                legend_title = legend_title + " " + units["Wind Speed"].strip()

            except (KeyError, ValueError):
                pass # If no units exists, or the config isn't valid, just use title without units

            legend.set_title(legend_title, prop={"size":8})
        except:
            raise

class Histogram:

    """ Implements plotting of generic histogram """

    def __init__(self):
        self.data = None
        self.label = ""


    def set_data(self, data, label):
        """
        Args:
        data - The data to display
        label - The label for the x-axis
        """
        self.data = data
        self.label = label

    def draw(self, fig):

        """ Draw histogram of current data on figure """

        axes = fig.add_subplot(111)
        axes.hist(self.data, 50, normed=1)

        axes.set_xlabel(self.label)
        axes.set_ylabel("Frequency (%)")
        axes.grid(True)

class Plotter:

    """ Implements standard plotting - three subplots of data vs. time """

    def __init__(self, configmanager):
        """ Initialise the plotter """
        self.suspend = False
        self.configmanager = configmanager
        self.clear_data()

    def suspend_draw(self, suspend):
        """
        Args:
        suspend - If true, updates to the plot will not cause the plot to automatically redraw
        """
        self.suspend = suspend

    def clear_data(self):
        """
        Clears all subplots and associated data
        Args: None
        """
        self.subplot_visible = [False, False, False]
        self.subplot_data = [None, None, None]

    def apply_units_to_axis_label(self, label):
        """
        Takes an axes label and applies a unit suffix from the class config member.
        (e.g. 'Humidity' might become 'Humidity %')
        Args:
        label - If this label exists in the config, returns the label with suffix applied
        """
        try:
            units = self.configmanager.get_units() # Get unit strings from config
            try:
                label = label + " " + units[label].strip() #Try adding a unit to the field name
            except KeyError:
                pass #If no unit exists, just use the field name

        except (KeyError, ValueError):
            pass # If no units exists, or the config isn't valid, just return the label as is.

        return label

    def set_dataset(self, times, dataset, axis_label, field_index):
        """
        For a particular subplot, set its data, timestamps and label.
        Args:
        times - the timestamps for the data
        dataset - the data
        axis_label - label for the y-axis (units will be applied)
        field_index - the subplot index (0 to 2). Values outside this range will produce no effects
        """

        if field_index < 3:
            axis_label = self.apply_units_to_axis_label(axis_label)
            self.subplot_data[field_index] = DataSet(axis_label, dataset, times)

    def set_visibility(self, plot_index, show):
        """
        Set the visibility of a plot
        Args:
        plot_index - the subplot index (0 to 2). Values outside this range will produce no effects
        show - True to show the plot, False to hide it
        """
        if plot_index < 3:
            self.subplot_visible[plot_index] = show

    def draw(self, fig, styles):

        """ Draws this plot on provided figure """
        if self.suspend:
            return # Drawing has been suspended

        fig.clf()

        first_axis = None
        plot_count = 0
        for idx in range(3):
            if self.subplot_visible[idx]: #Only show visible plots

                get_module_logger().info("Plotting index %d with style options %s", idx, ",".join(styles[idx]))
                #sharex parameter means axes will zoom as one w.r.t x-axis
                axis = fig.add_subplot(self.visible_count, 1, plot_count+1, sharex=first_axis)

                axis.tick_params(axis='both', which='major', labelsize=10)
                if styles[idx][0] == "line":
                    axis.plot(
                        self.subplot_data[idx].times, self.subplot_data[idx].data, color=styles[idx][1])
                elif styles[idx][0] == "bar":
                    axis.bar(
                        self.subplot_data[idx].times, self.subplot_data[idx].data,
                        align="center", width=(10/86400), color=styles[idx][1], edgecolor=styles[idx][1])

                axis.set_ylabel(self.subplot_data[idx].ylabel, fontsize=10)

                #Save the first subplot so that other plots can share its x axis
                first_axis = axis if idx == 0 else first_axis

                #Keep track of number of visible plots
                plot_count += 1

        fig.autofmt_xdate() # Nice formatting for dates (diagonal, only on bottom axis)

    @property
    def visible_count(self):
        """ Return the number of currently visible subplots """
        return self.subplot_visible.count(True)
