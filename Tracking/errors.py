class TrackingFailure(Exception):
    """Generic tracking failure, subclassed by more specific
    exceptions.
    """
    pass


class TrackingApiFailure(TrackingFailure):
    """Raised in the event of a failure with the service's API. For
    example, a SOAP fault or authentication failure. The request was
    valid but the service API returned an error.
    """
    pass


class TrackingNetworkFailure(TrackingFailure):
    """Raised for network communication failure when talking to the
    service API. For example, a network timeout or DNS resolution
    failure.
    """
    pass


class TrackingNumberFailure(TrackingFailure):
    """Raised when the request to the service API was successful, but
    the service didn't recognize the tracking number. For example the
    tracking number wasn't in the service database, even though it looks like a
    valid tracking number for the service.
    """
    pass


class UnsupportedTrackingNumber(TrackingFailure):
    """Raised when a tracking number cannot be matched to a service.
    """
    pass


class InvalidTrackingNumber(TrackingFailure):
    """Raised when a service's track() method is called with a TN not for that
    service
    """
    pass


class UnsupportedCarrier(TrackingFailure):
    """Raised when a carrier cannot be matched to a registered carrier.
    """
    pass