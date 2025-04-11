"""TimeType class.
"""
import time


class TimeType:
    """Holds various representations of a point in time.
    """
    def __init__(self):
        """Constructor
        """
        self.current_time_seconds_float: float = time.time()
        self.current_time_seconds_int: int = int(self.current_time_seconds_float)
        self.current_time_human_readable: str = f"{time.ctime(self.current_time_seconds_float)} (UTC)"

    def set_time(self, time_seconds: float):
        """Sets the internal time values.

        :param time_seconds: The time in seconds to set.
        :type: float
        """
        self.current_time_seconds_float = time_seconds
        self.current_time_seconds_int = int(time_seconds)
        self.current_time_human_readable  = f"{time.ctime(time_seconds)} (UTC)"
