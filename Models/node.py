from event import Event

class Node:
  # ------------------------
  #       CONSTRUCTOR
  # ------------------------
  def __init__(self, id: int, event: Event):
    self.__id: int = id
    self.__event: Event = event
    self.__father: Node = None
    self.__right_son: Node = None
    self.__left_son: Node = None
    self.__height: int = 0

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
  def father(self) -> Node:
    return self.__father

  @father.setter
  def father(self, value: Node) -> None:
    self.__father = value

  @property
  def right_son(self) -> Node:
    return self.__right_son

  @right_son.setter
  def right_son(self, value: Node) -> None:
    self.__right_son = value

  @property
  def left_son(self) -> Node:
    return self.__left_son

  @left_son.setter
  def left_son(self, value: Node) -> None:
    self.__left_son = value

  @property
  def height(self) -> int:
    return self.__height
      
# ------------------------
#         METHODS
# ------------------------

  def update_height(self):
    pass

  def is_leaf(self) -> bool:
    return self.__left_son is None and self.__right_son is None
  
  def get_key(self):
    return (self.__event.priority, self.__event.magnitude, self.__event.id)
  
  def balance_factor(self) -> int:
    left_h = self.__left_son.__height if self.__left_son else -1
    right_h = self.__right_son.__height if self.__right_son else -1
    return left_h - right_h

  # --------------------------------------------------------
  # MÉTODOS MÁGICOS DE COMPARACIÓN (SOBRECARGA DE OPERADORES)
  # --------------------------------------------------------

  def __lt__(self, other: Node) -> bool:
    return self.get_key() < other.get_key()

  def __gt__(self, other: Node) -> bool:
    return self.get_key() > other.get_key()

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, Node):
        return False
    return self.get_key() == other.get_key()