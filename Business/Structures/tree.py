from abc import ABC, abstractmethod
try:
  from Models.node import Node
except (ImportError, ValueError):
  try:
    from ...Models.node import Node
  except (ImportError, ValueError):
    from node import Node


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
      if current.left_son is not None:
        current.left_son.father = current
    elif new_node > current:
      current.right_son = self._insert_recursive(current.right_son, new_node)
      if current.right_son is not None:
        current.right_son.father = current
    else:
      return current
    return self._post_process(current)

  @abstractmethod
  def _post_process(self, node: Node) -> Node:
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
      self.__root = self._delete_helper(self.__root, key)
      
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
      if current.left_son is not None:
        current.left_son.father = current
    # If the key is greater, search in the right side
    elif key > current_key:
      current.right_son = self._delete_helper(current.right_son, key)
      if current.right_son is not None:
        current.right_son.father = current
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
        current.left_son.father = current.father
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
        if current.left_son is not None:
          current.left_son.father = current
    
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
  
  def preorder(self, start_node: Node | None = None) -> list[Node]:
    result_list: list[Node] = []
    root_to_use = start_node if start_node is not None else self.root
    self._preorder_recursive(root_to_use, result_list)
    return result_list
  
  def _preorder_recursive(self, current: Node, result: list[Node]) -> None:
    if current is not None:
      result.append(current)
      self._preorder_recursive(current.left_son, result)
      self._preorder_recursive(current.right_son, result)


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

    #height of the Tree
  def height(self):
    return self.root.height if self.root is not None else -1

  # Traverses the tree and returns a list of tuples: (Node, Depth)
  def get_all_nodes_with_depth(self, current_node: Node | None = None, current_depth: int = 0) -> list[tuple[Node, int]]:
    """
    Traverses the tree and returns a list of tuples: (Node, Depth).
    The root node has depth 0, its children depth 1, and so on.
    If current_node is omitted, traversal starts from self.root.
    """
    if current_node is None:
      current_node = self.root
    if current_node is None:
      return []

    nodes: list[tuple[Node, int]] = [(current_node, current_depth)]
    if current_node.left_son is not None:
      nodes.extend(self.get_all_nodes_with_depth(current_node.left_son, current_depth + 1))
    if current_node.right_son is not None:
      nodes.extend(self.get_all_nodes_with_depth(current_node.right_son, current_depth + 1))
    return nodes
  def get_node_metrics(self, search_key: tuple[int, float, int]) -> dict:
        """
        Returns a dictionary containing the depth, height, and balance factor of the node with the given search_key.
        """
        current = self.root
        depth = 0
        
        while current is not None:
            current_key = current.get_key()
            
            # 1. Node found
            if search_key == current_key:
                # Rule: Height of empty tree is -1
                left_h = current.left_son.height if current.left_son else -1
                right_h = current.right_son.height if current.right_son else -1
                
                balance_factor = left_h - right_h
                
                return {
                    "depth": depth,
                    "height": current.height,
                    "balance_factor": balance_factor
                }
            elif search_key < current_key:
                current = current.left_son
            else:
                current = current.right_son
                
            depth += 1 # Increse depth as we go down the tree
        return 
