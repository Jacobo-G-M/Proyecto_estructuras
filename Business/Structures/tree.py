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
  def insert(self, new_node: Node) -> None:
    self.root = self._insert_recursive(self.root, new_node)

  def _insert_recursive(self, current: Node, new_node: Node) -> Node:
    #Base case: if the current node is None, we found the position to insert the new node
    if current is None:
      return new_node
    #Comparison: decide whether to go left or right in the tree based on the new node's value
    if new_node < current:
      current.left_son = self._insert_recursive(current.left_son, new_node)
    elif new_node > current:
      current.right_son = self._insert_recursive(current.right_son, new_node)
    else:
      return current
    return self._balance_node(current)

  @abstractmethod
  def _balance_node(self, node: Node) -> Node:
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

