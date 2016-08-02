
from operator import attrgetter


class TrackingInfo:

    def __init__(self, tracking_number, delivery_date=None, is_delivered=False, **kwargs):
        # indict = {}
        # dict.__init__(self, indict)
        self.tracking_number = tracking_number
        self.delivery_date = delivery_date
        self.is_delivered = is_delivered
        self.events = []
        # self.update(kwargs)

    # def __getattr__(self, name):
    #     return self[name]
    #
    # def __setattr__(self, name, val):
    #     self[name] = val

    @property
    def location(self):
        """A shortcut to the location of the latest event for this package
        """
        return self.events[-1].location

    @property
    def last_update(self):
        """Shortcut to the timestamp of the latest event for this package
        """
        return self.events[-1].timestamp

    @property
    def status(self):
        """Shortcut to the detail of the latest event for this package
        """
        return self.events[-1].detail

    def create_event(self, timestamp, location, detail, **kwargs):
        """Create a new event with these attributes, events do not need to be added
        in order
        """
        event = TrackingEvent(timestamp, location, detail)
        # event.update(kwargs)
        return self.add_event(event)

    def add_event(self, event):
        """Add a new TrackingEvent object to this package, events do not need to
        be added in order
        """
        self.events = self.sort_events(self.events + [event])
        return event

    def sort_events(self, events=None):
        """Sort a list of events by timestamp, defaults to this package's events
        """
        if events is None:
            events = self.events
        return sorted(events, key=attrgetter('timestamp'))


class TrackingEvent:
    """An individual tracking event, like a status change
    Only the timestamp, location, and detail attributes are required, but a
    carrier may add other information if available. timestamp is always a
    datetime object.
    """
    _repr_template = '<TrackingEvent(timestamp={ts}, location={e.location!r}, detail={e.detail!r})>'

    def __init__(self, timestamp, location, detail, **kwargs):
        self.timestamp = timestamp
        self.location = location
        self.detail = detail
        # self.update(kwargs)
    #
    # def __getattr__(self, name):
    #     return self[name]
    #
    # def __setattr__(self, name, val):
    #     self[name] = val

    def __repr__(self):
        return self._repr_template.format(e=self, ts=self.timestamp.isoformat())

