#! /usr/bin/env python3

"""Chat widget for the WebUI."""

from streambot.service.builtin.webui.widgets import base


class Widget(base.Widget):
    name = "timer"
    display_name = "Timer"
    description = "Displays a countdown timer."

    # active = True

