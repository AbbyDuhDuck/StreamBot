#! /usr/bin/env python3

"""
Simple Stream Bot

This package contains the source code for an event driven bot for live 
streaming. It's designed for use with Youtube and Twitch, and made for 
easy programmatic customization. There are plans to add a more robust 
UI beyond the chat UI that is currently implemented. 

Modules & Subpackages:
----------------------
- TODO

Usage:
------
Run the bot using `python src/main.py <name>` where the name is your 
config files in `usr/<name>` - there is an example setup included to 
show how to expand the usage and functionallity of the bot.
"""

from . import service
from . import signals
from . import usr

# EOF #
