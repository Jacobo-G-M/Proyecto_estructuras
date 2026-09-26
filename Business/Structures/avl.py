from tree import Tree
from ...Models.node import Node

class AVL(Tree):
  # ------------------------
  #       CONSTRUCTOR
  # ------------------------
  def __init__(self, id: int, stress_mode: bool = False):
    super().__init__(id)
    self.__stress_mode: bool = stress_mode
    self.__cases = {"LL": 0, "RR": 0, "LR": 0, "RL": 0}
    self.__turns = {"left": 0, "right": 0}
    
  # ------------------------
  #   GETTERS AND SETTERS
  # ------------------------
  @property
  def stress_mode(self) -> bool:
    return self.__stress_mode

  @stress_mode.setter
  def _stress_mode(self, value: bool) -> None:
    self.__stress_mode = value
    
  @property
  def cases(self) -> dict[str, int]:
    return self._cases

  @property
  def turns(self) -> dict[str, int]:
    return self._turns
  # ------------------------
  #         METHODS
  # ------------------------
  #main method for retores_balace after stress_mode -----
  def restore_balance(self) -> None:

    #verifies that the tree exists
    if self.root is None:
      return

    #starts the traversal from the bottom and returns the new root balanced
    self.root = self._restore_node(self.root)

    #cuts of its relations
    if self.root is not None:
      self.root.father = None

    #turn off stress_mode
    self.stress_mode = False

  #recursive method for restore the tree's balance
  def _restore_node(self, current_node):
    if current_node is None:
      return None

    # Step A: Restore children subtrees first (Post-order: Left and Right)
    current_node.left_son = self._restore_node(current_node.left_son)
    if current_node.left_son is not None:
      current_node.left_son.father = current_node

    current_node.right_son = self._restore_node(current_node.right_son)
    if current_node.right_son is not None:
      current_node.right_son.father = current_node

    # Step B: Update the current node's height with the updated children's heights
    current_node.update_height()

    # Step C: Resolve imbalances (handles balance factors greater than 2)
    # While the balance factor is outside {-1, 0, 1}, keep balancing
    while abs(current_node.balance_factor()) > 1:
      current_node = self.balance(current_node)
      current_node.update_height()

    return current_node

  
  # Protected method to delete a node. It uses a similar logic in the tree class, but it also balances the tree
  def _delete_helper(self, current: Node | None, key: tuple[int, float, int]) -> Node | None:
    node = super()._delete_helper(current, key)
    # Check if the node exists
    if node is None:
      return None
    
    # If the node exists, it updates its height
    node.update_height()
    
    # If stress mode is active, postpone rotations (keep only BST order)
    if self.__stress_mode:
      return node
    # In normal mode, balance node-by-node
    return self.balance(node)
    #Template Method Hook
    def _post_process(self, node: Node) -> Node:
      return self.balance(node)

    # Method to balance a specific node (local balancing)
  def balance(self, node: Node | None) -> Node | None:
    if node is None:
      return None

    # Update node height before checking balance factor
    node.update_height()

    # Get the balance factor (left_height - right_height)
    bf = node.balance_factor()

    # Check Left-Heavy cases (bf > 1)
    if bf > 1:
      # Left-Right (LR) Case: child is right-heavy
      if node.left_son and node.left_son.balance_factor() < 0:
        self._cases["LR"] += 1
        node.left_son = self.left_rotation(node.left_son)
      # Left-Left (LL) Case: single right rotation
      else:
        self._cases["LL"] += 1
        return self.right_rotation(node)

    # Check Right-Heavy cases (bf < -1)
    if bf < -1:
      # Right-Left (RL) Case: child is left-heavy
      if node.right_son and node.right_son.balance_factor() > 0:
        self._cases["RL"] += 1
        node.right_son = self.right_rotation(node.right_son)
      # Right-Right (RR) Case: single left rotation
      else:
        self._cases["RR"] += 1
        return self.left_rotation(node)

    # If already balanced, return the unchanged node
    return node
  
    # Method to perform a right rotation (LL case)
  def right_rotation(self, node: Node) -> Node:
    # Identify nodes
    new_root = node.left_son
    new_root_right_son = new_root.right_son

    # Reassign children
    new_root.right_son = node
    node.left_son = new_root_right_son

    # Reassign parents (father references)
    new_root.father = node.father
    node.father = new_root
    if new_root_right_son is not None:
      new_root_right_son.father = node

    # Update heights (bottom-up: old root first, then new root)
    node.update_height()
    new_root.update_height()
    # Update counter for right turns
    self.__turns["right"] += 1

    # Return new subtree root
    return new_root

  # Method to perform a left rotation (RR case)
  def left_rotation(self, node: Node) -> Node:
    # Identify nodes
    new_root = node.right_son
    new_root_left_son = new_root.left_son

    # Reassign children
    new_root.left_son = node
    node.right_son = new_root_left_son

    # Reassign parents (father references)
    new_root.father = node.father
    node.father = new_root
    if new_root_left_son is not None:
      new_root_left_son.father = node

    # Update heights (bottom-up: old root first, then new root)
    node.update_height()
    new_root.update_height()
    # Update counter for left turns
    self.__turns["left"] += 1

    # Step 5: Return new subtree root
    return new_root
