
from operator import attrgetter
import collections


class TrackingInfo(collections.MutableMapping):

    def __init__(self, tracking_number, delivery_date=None, is_delivered=False, **kwargs):
        # indict = {}
        # dict.__init__(self, indict)
        self.tracking_number = tracking_number
        self.delivery_date = delivery_date
        self.is_delivered = is_delivered
        # self.expected_delivery_date =
        self._events = []

        self.store = dict()
        self.update(kwargs)

        if self.tracking_number is None:
            self.create_event(None, None, None)


    def __getitem__(self, key):
        return self.store[self._keytransform_(key)]


    def __setitem__(self, key, value):
        self.store[self._keytransform_(key)] = value


    def __delitem__(self, key):
        del self.store[self._keytransform_(key)]


    def __iter__(self):
        return iter(self.store)


    def __len__(self):
        return len(self.store)


    def _keytransform_(self, key):
        return key


    # def __getattr__(self, name):
    #     return self[name]
    #
    # def __setattr__(self, name, val):
    #     self[name] = val

    def __eq__(self, other):
        if isinstance(other, TrackingInfo):
            return other.last_update == self.last_update
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result


    @property
    def events(self):
        """

        :return:
        :rtype: list[TrackingEvent]
        """
        return self._events

    @events.setter
    def events(self, value):
        self._events = value


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

