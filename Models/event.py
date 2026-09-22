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
    return self.__attention_state()

  @attention_state.setter
  def attention_state(self, value: str) -> None:
    self.__attention_state = value

  @property
  def status(self) -> str:
    return self.__status

  @status.setter
  def _status(self, value: str) -> None:
    self.__status = value

# ------------------------
#         METHODS
# ------------------------
