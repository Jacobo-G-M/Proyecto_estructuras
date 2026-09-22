from abc import ABC, abstractmethod
from ...Models.node import Node

class Tree(ABC):
  # ------------------------
  #       CONSTRUCTOR
  # ------------------------
  def __init__(self, id: int):
    self.__id: int = id
    self.__root: Node = None
    
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
  def root(self) -> Node:
    return self.__root

  @root.setter
  def root(self, value: Node) -> None:
    self.__root = value

  # ------------------------
  #         METHODS
  # ------------------------
  def insert(self):
    pass

  def delete(self):
    pass

  def preorder(self):
    pass

  def inorder(self):
    pass

  def postorder(self):
    pass

  def width(self):
    pass

  def update_height(self):
    pass

