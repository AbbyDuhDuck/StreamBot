import importlib.util
from pathlib import Path

from .bridge import EventBridge
from streambot.signals import EventBus, QueryBus

from .base import Widget


class WidgetManager:

    def __init__(self, builtin_dir, user_dir):

        self.builtin_dir = Path(builtin_dir)
        self.user_dir = Path(user_dir)

        self.widgets: list[Widget] = []

        self.events = set()
        self.queries = set()

        self.event_lookup = {}
        self.query_lookup = {}

    def get_widget(self, name) -> Widget | None:
        for widget in self.widgets:
            if widget.name == name:
                return widget
        return None
    
    def register_events(self, event_bus: EventBus):
        for widget in self.widgets:
            widget.register_events(event_bus)

    def register_queries(self, query_bus: QueryBus):
        for widget in self.widgets:
            widget.register_queries(query_bus)

    # ------------------------------------------------
    # Discovery
    # ------------------------------------------------

    def discover(self):

        builtin = self._scan(self.builtin_dir)
        user = self._scan(self.user_dir)

        widgets = builtin
        widgets.update(user)

        return widgets

    def _scan(self, base):

        found = {}

        print(f"Scanning for widgets in {base}...")

        if not base.exists():
            return found

        for folder in base.iterdir():

            if not folder.is_dir():
                continue

            widget_py = folder / "widget.py"

            if widget_py.exists():
                found[folder.name] = widget_py

        return found

    # ------------------------------------------------
    # Load widgets
    # ------------------------------------------------

    def load(self, event_bridge: EventBridge):

        widget_files = self.discover()

        for name, path in widget_files.items():

            spec = importlib.util.spec_from_file_location(
                f"widget_{name}", path
            )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            widget_class: type[Widget] = getattr(module, "Widget")

            widget = widget_class()

            widget.name = name
            widget.path = path.parent
            widget.api = event_bridge

            self.widgets.append(widget)

            self.events.update(widget.EVENTS)
            self.queries.update(widget.QUERIES)

        self._build_lookups()

        print(f"Loaded {len(self.widgets)} widgets: {', '.join(w.name for w in self.widgets)}")

    # ------------------------------------------------
    # Lookup tables
    # ------------------------------------------------

    def _build_lookups(self):

        self.event_lookup = {
            e.__name__: e
            for e in self.events
        }

        self.query_lookup = {
            q.__name__: q
            for q in self.queries
        }

    # ------------------------------------------------
    # Event resolution
    # ------------------------------------------------

    def resolve_event(self, name):

        return self.event_lookup.get(name)

    def resolve_query(self, name):

        return self.query_lookup.get(name)
