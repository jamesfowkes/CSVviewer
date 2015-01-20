"""
app_info.py

@author: James Fowkes

Define constants for requests coming from the GUI
"""

class REQS:
    #pylint: disable=no-init
    #pylint: disable=too-few-public-methods
    """ Add request ID numbers sequentially """
    CHANGE_SUBPLOT1 = 0
    CHANGE_SUBPLOT2 = 1
    CHANGE_SUBPLOT3 = 2
    AVERAGE_SUBPLOT_DATA = 3
    RESET_SUBPLOT_DATA = 4
    SPECIAL_OPTION = 5
    NEW_DATA = 6
    ABOUT_DIALOG = 7
    GET_SPECIAL_ACTIONS = 8
    GET_PLOTTING_STYLE = 9

