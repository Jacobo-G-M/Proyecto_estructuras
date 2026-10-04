from datetime import datetime

class Event:
  # ------------------------
  #       CONSTRUCTOR
  # ------------------------
  def __init__(self, id: int, priority: int, magnitude: float, depth: float, epicenter: tuple[float, float], date_time: datetime, review: int, attention_state: str ="Pending", status: str ="Active"):
    self.__id: int = id
    self.__priority: int = priority
    self.__magnitude: float = magnitude
    self.__depth: float = depth
    self.__epicenter: tuple[float, float] = epicenter
    self.__date_time: datetime = date_time
    self.__review: int = review
    self.__attention_state: str = attention_state
    self.__status: str = status
    self.__origin_stations: list = []

  # ------------------------
  #   GETTERS AND SETTERS
  # ------------------------
  @property
  def id(self) -> int:
    return self.__id

  @id.setter
  def id(self, value: int) -> None:
    self.__id = value

  @property
  def priority(self) -> int:
    return self.__priority
    
  @priority.setter
  def priority(self, value: int) -> None:
    self.__priority = value

  @property
  def magnitude(self) -> float:
    return self.__magnitude

  @magnitude.setter
  def magnitude(self, value) -> None:
    self.__magnitude = value

  @property
  def depth(self) -> float:
    return self.__depth

  @depth.setter
  def depth(self, value) -> None:
    self.__depth = value

  @property
  def epicenter(self) -> tuple[float, float]:
    return self.__epicenter

  @epicenter.setter
  def epicenter(self, value: tuple[float, float]) -> None:
    self.__epicenter = value

  @property
  def date_time(self) -> datetime:
    return self.__date_time

  @date_time.setter
  def date_time(self, value: datetime) -> None:
    self.__date_time = value

  @property
  def review(self) -> int:
    return self.__review

  @review.setter
  def review(self, value: int) -> None:
    self.__review = value

  @property
  def attention_state(self) -> str:
    return self.__attention_state

  @attention_state.setter
  def attention_state(self, value: str) -> None:
    self.__attention_state = value

  @property
  def status(self) -> str:
    return self.__status

  @status.setter
  def status(self, value: str) -> None:
    self.__status = value

  @property
  def origin_stations(self) -> list:
    return self.__origin_stations

  @origin_stations.setter
  def origin_stations(self, value: list) -> None:
    if isinstance(value, list):
      self.__origin_stations = value
    else:
      raise TypeError("origin_stations must be a list.")

  # Alias for compatibility with singular references
  @property
  def origin_station(self) -> list:
    return self.__origin_stations

# ------------------------
#         METHODS
# ------------------------

  def add_origin_station(self, station) -> None:
    """Adds an origin station to the event if not already present."""
    st_id = getattr(station, 'id', station)
    for existing in self.__origin_stations:
      existing_id = getattr(existing, 'id', existing)
      if existing_id == st_id:
        return
    self.__origin_stations.append(station)

  def get_key(self) -> tuple[int, float, int]:
    """Returns the sorting key K = (Priority, Magnitude, ID) according to domain rules."""
    return (self.__priority, self.__magnitude, self.__id)
