# Python 3.6
# Encoding: UTF-8
# Date created: 17.08.2018
# Author: Robert Simpson (robert_zwilling@web.de)
# License: MIT

import json


def read_or_create(default_separator=':'):
    """
    Look for board dictionary file. This file allows a user to specify human readable names for Phidget
    boards based on their serial-number. It also allows the specification of the separator used in between
    the board name and the channel name in the column header of the resulting *.csv file.
    If the file does not exist, create an empty template.

    :param default_separator: Default separator character to be used (default=':')
    :type default_separator: str
    :return: Board-dictionary and separator
    :rtype: tuple
    """

    board_dict = {'serial_nr': 'name string'}
    separator = default_separator

    try:
        with open('board_dictionary.json', mode='r') as dict_for_read:
            [separator, board_dict] = json.load(dict_for_read)
    except FileNotFoundError as e:
        with open('board_dictionary.json', mode='w') as dict_for_write:
            json.dump([separator, board_dict], dict_for_write, indent=4)
            board_dict = {}
    except OSError as e:
        print(e)
        exit(1)

    return board_dict, separator
