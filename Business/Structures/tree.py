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

  @abstractmethod
  def delete(self, id_event: int) -> None:
    pass
  
  def preorder(self) -> list[Node]:
    result_list: list[Node] = []
    self._preorder_recursive(self.root, result_list)
    return result_list

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
  def _preorder_recursive(self, current: Node, result: list[Node]) -> None:
    if current is not None:
      result.append(current)
      self._preorder_recursive(current.left_son, result)
      self._preorder_recursive(current.right_son, result)


    #posorder traversal METHOD -----
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