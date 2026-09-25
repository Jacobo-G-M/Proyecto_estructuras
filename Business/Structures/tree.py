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

    #posroder traversal METHOD -----
  def postorder(self):
    if self.root is None:
      print("Tree is empty")
      return []
    else:
      traversal = []
      self._postorder(traversal, self.root)
      return traversal

  def _postorder(self, traversal, current_node):
    if current_node.left_son is not None:
      self._postorder(traversal, current_node.left_son)

    if current_node.right_son is not None:
      self._postorder(traversal, current_node.right_son)

    traversal.append(current_node)

    return traversal

    #width traversal METHOD
  def width(self):
    tree_root = self.root
    if tree_root is None:
      print("Tree is empty")
      return []
    else:
      return self._width( tree_root)

  def _width(self, current_node):
    queue = []
    traversal = []
    queue.append(current_node)

    while len(queue) > 0:
      node = queue.pop(0)
      traversal.append(node)
      if node.left_son is not None:
        queue.append(node.left_son)
      if node.right_son is not None:
        queue.append(node.right_son)
  
    return traversal

    #update height of specific Nodes from Tree
  def update_height(self, node: Node):
    if node is not None:
      node.update_height

    #height of the Tree
  def height(self):
    return self.root.height if self.root is not None else -1