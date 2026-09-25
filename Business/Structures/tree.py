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

  # Public method to delete a node. It returns a node to save it in the undo stack
  def delete(self, key: tuple[int, float, int]) -> Node | None:
    # Check if the tree is empty
    if self.__root is None:
      return None
    
    # Check if the key exists
    deleted_node = self.search_node(key)
    if deleted_node is None:
      return None
    else:
      # Uses the private method to apply the rest of the logic
      self._delete_helper(deleted_node, key)
      
      # If the root has changed, it has to updates its father to None
      if self.__root is not None:
        self.__root.father = None
      # Returns the deleted node to use it in the undo stack
      return deleted_node
  
  # Protected method to delete a node.
  def _delete_helper(self, current: Node | None, key: tuple[int, float, int]) -> Node | None:
    # Base case: if the node is empty, it does not have to delete anything
    if current is None:
      return None
    
    # Get the key of the current node
    current_key = current.get_key()
    
    # If the key is smaller, search in the left side
    if key < current_key:
      current.left_son = self._delete_helper(current.left_son, key)
    # If the key is greater, search in the right side
    elif key > current_key:
      current.right_son = self._delete_helper(current.right_son, key)
    # The node to delete has been found
    else:
      # Case 1: is a leaf
      if current.is_leaf():
        return None
      # Case 2: It only has a child
      elif current.left_son is None:
        # Update its father
        current.right_son.father = current.father
        # Only has a right son. Returns the right son
        return current.right_son
      elif current.right_son is None:
        # Update its father
        current.left_son = current.father
        # Only has a left son. Returns the left son
        return current.left_son
      # Case 3: It has two children
      else:
        # Finds its succesor by taking the maximum key from its left tree
        succesor = self._max_node(current.left_son)
        # Replace the values of the deleted node with those of its succesor
        current.id = succesor.id
        current.event = succesor.event
        # Delete the copied succesor
        current.left_son = self._delete_helper(current.left_son, succesor.get_key())
    
    # Returns the current node
    return current
        
  # Auxiliary method for finding the largest node in a subtree
  def _max_node(self, node: Node) -> Node:
    # Saves the current node
    current = node
    # Iterate through the right node until there are no more
    while current.right_son is not None:
      # Saves the new largest right node
      current = current.right_son
    # Returns the largest node found
    return current
  
  # Public method to search a node by key
  def search_node(self, key: tuple[int, float, int]) -> Node | None:
    return self._search_node_helper(self.__root, key)

  # Protected method to search a node by key
  def _search_node_helper(self, current: Node | None, key: tuple[int, float, int]) -> Node | None:
    # Base case 1: Empty tree or we came to an empty branch
    if current is None:
      return None

    # Get the key of the node
    current_key = current.get_key()

    # Base case 2: Node found
    if key == current_key:
      return current
    # Goes to the left son  
    elif key < current_key:
      return self._search_node_helper(current.left_son, key)
    # Goes to the right son
    else:
      return self._search_node_helper(current.right_son, key)

  def preorder(self):
    pass
  
  # Method to do a in-order iteration in a tree
  def inorder(self) -> list[Node]:
    # The list that we will return the method
    result = []
    # Use the private method that contains the rest of the logic
    self._inorder(self.__root, result)
    return result
    
  # Protected method for in-order iteration. It uses recursion
  def _inorder(self, node: Node, result: list[Node]) -> None:
    # Check if the current node exists
    if node is None:
      return
    # Apply recursion to the left son of the node
    self._inorder(node.left_son, result)
    # Add the current node to the result list
    result.append(node)
    # Apply recursion to the right son of the node
    self._inorder(node.right_son, result)


  def postorder(self):
    pass

  def width(self):
    pass

  def update_height(self):
    pass

