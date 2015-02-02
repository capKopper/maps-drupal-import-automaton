"""Source identifier class."""
import abc


class SourceIdentifierInterface(object):
    """Abstract class definition."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_pattern(self):
        pass


class SourceIdentifierTimestamp(SourceIdentifierInterface):
    """Implementation for a timestamp identifier."""

    def __init__(self, id, prefix, format):
        self.id = id
        self.id_prefix = prefix
        self.format = format

    def get_pattern(self):
        return self.format.replace(self.id_prefix + self.id, "([0-9]+)")
