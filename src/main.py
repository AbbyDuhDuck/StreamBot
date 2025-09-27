#! /usr/bin/env python3

"""
# Simple Stream Bot

Main Entry Point for the program!
    
Usage: `python main.py <user>`

The user is the profile to launch, located in `usr/<user>/`
"""

# -=-=- Imports & Globals -=-=- #

import sys
import importlib
from pathlib import Path

from bot import UserSettings

# Add project root (one level above src/) to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# -=-=-=- MAIN -=-=-=- #

def main():
    """
    Main Entry Point for the program!

    Launches the bot using the provided settings and services that are
    defined in the user profile's folder (`usr/<user>/`). It loads the
    provided settings as a module and then runs the `UserSettings` run
    method if such an object exists.
    
    Usage:
    ------ 
    `python main.py <user>`
    
    The user is the profile that is to be launched is to be located in 
    `usr/<user>/__init__.py` and a `SETTINGS:UserSettings` variable
    should be defined and set up, this object is used to run the bot.
    (See. `usr/example/__init__.py` for an example setup)
    """

    # Get the user argument
    if len(sys.argv) < 2:
        print("Usage: python main.py <user>")
        sys.exit(1)
    user = sys.argv[1]

    # Ensure usr/ is importable
    sys.path.append(str(Path(__file__).resolve().parent.parent / "usr"))

    # Import the user as a module
    try:
        user_module = importlib.import_module(f"{user}")
    except ModuleNotFoundError as e:
        # print(e)
        print(f"No such user module: {user}")
        sys.exit(1)

    # Grab the settings object and run it
    if hasattr(user_module, "SETTINGS"):
        # TODO: ensure that user_module.SETTINGS is a UserSettings type
        settings:UserSettings = user_module.SETTINGS
        settings.run()
    else:
        print(f"User module '{user}' has no User Settings.")

if __name__ == "__main__":
    main()

# EOF #
