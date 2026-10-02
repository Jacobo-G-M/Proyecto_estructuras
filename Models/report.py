from datetime import datetime

try:
    import Models.station as station_module
except ImportError:
    import station as station_module

class Report:
    def __init__(
        self,
        id: int,
        magnitude: float,
        depth: float,
        epicenter: tuple[float, float],
        date_time: datetime,
        review: int,
        origin_station: list = None,
    ):
        self.id = id
        self.magnitude = magnitude
        self.depth = depth
        self.epicenter = epicenter
        self.date_time = date_time
        self.review = review
        self.origin_station = origin_station if origin_station is not None else []

    # --- id ---
    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("id must be an integer.")
        self._id = value

    # --- magnitude ---
    @property
    def magnitude(self) -> float:
        return self._magnitude

    @magnitude.setter
    def magnitude(self, value: float):
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError("magnitude must be a float.")
        self._magnitude = float(value)

    # --- depth ---
    @property
    def depth(self) -> float:
        return self._depth

    @depth.setter
    def depth(self, value: float):
        if not isinstance(value, (float, int)) or isinstance(value, bool):
            raise TypeError("depth must be a float.")
        self._depth = float(value)

    # --- epicenter ---
    @property
    def epicenter(self) -> tuple[float, float]:
        return self._epicenter

    @epicenter.setter
    def epicenter(self, value: tuple[float, float]):
        self._epicenter = self._validate_coord(value, "epicenter")

    # --- date_time ---
    @property
    def date_time(self) -> datetime:
        return self._date_time

    @date_time.setter
    def date_time(self, value: datetime):
        if not isinstance(value, datetime):
            raise TypeError("date_time must be an instance of datetime.")
        self._date_time = value

    # --- review ---
    @property
    def review(self) -> int:
        return self._review

    @review.setter
    def review(self, value: int):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("review must be an integer.")
        self._review = value

    # --- origin_station ---
    @property
    def origin_station(self) -> list:
        return self._origin_station

    @origin_station.setter
    def origin_station(self, value: list):
        if not isinstance(value, list):
            raise TypeError("origin_station must be a list.")
        if not all(isinstance(item, station_module.Station) for item in value):
            raise TypeError("all items in origin_station must be instances of Station.")
        self._origin_station = value

    # Internal helper method to validate coordinate tuples
    def _validate_coord(self, coord: tuple[float, float], field_name: str) -> tuple[float, float]:
        if not isinstance(coord, tuple) or len(coord) != 2:
            raise ValueError(f"{field_name} must be a tuple of exactly 2 elements (float, float).")
        return (float(coord[0]), float(coord[1]))

    def __repr__(self) -> str:
        station_ids = [s.id for s in self._origin_station if hasattr(s, "id")]
        return (
            f"Report(id={self._id}, magnitude={self._magnitude}, "
            f"depth={self._depth}, epicenter={self._epicenter}, "
            f"date_time={self._date_time}, review={self._review}, "
            f"origin_station_ids={station_ids})"
        )

    #--- methods ---

    #method to add an origin station
    def add_origin_station(self, station):
        if not isinstance(station, station_module.Station):
            raise TypeError("station must be an instance of Station.")
        if station not in self._origin_station:
            self._origin_station.append(station)

    def is_empty():
        pass
