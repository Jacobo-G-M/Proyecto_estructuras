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

  @abstractmethod
  def delete(self, id_event: int) -> None:
    pass

  def preorder(self):
    pass
  
  # Method to do a in-order iteration in a tree
  def inorder(self) -> list[Node]:
    # The list that we will return the method
    result = []
    # Use the private method that contains the rest of the logic
    self.__inorder(self.__root, result)
    return result
    
  # Private method for in-order iteration. It uses recursion
  def __inorder(self, node: Node, result: list[Node]) -> None:
    # Check if the current node exists
    if node is None:
      return
    # Apply recursion to the left son of the node
    self.__inorder(node.left_son, result)
    # Add the current node to the result list
    result.append(node)
    # Apply recursion to the right son of the node
    self.__inorder(node.right_son, result)


  def postorder(self):
    pass

  def width(self):
    pass

  def update_height(self):
    pass

