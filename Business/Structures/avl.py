from typing import Callable
from Business.Structures.tree import Tree
from Models.node import Node

class AVL(Tree):
  # ------------------------
  #       CONSTRUCTOR
  # ------------------------
  def __init__(self, id: int, stress_mode: bool = False, on_rotation = None):
    super().__init__(id)
    self.__stress_mode: bool = stress_mode
    self.__on_rotation: Callable[[str | None, str | None], None] = on_rotation  # Decoupled notification callback
    
  # ------------------------
  #   GETTERS AND SETTERS
  # ------------------------
  @property
  def stress_mode(self) -> bool:
    return self.__stress_mode

  @stress_mode.setter
  def stress_mode(self, value: bool) -> None:
    self.__stress_mode = value

  # ------------------------
  #         METHODS
  # ------------------------
  # Hook for template method in Tree: rebalances after recursive insertion
  def _post_process(self, node: Node) -> Node:
    node.update_height()
    if self.__stress_mode:
      return node  # Skip balancing in stress mode
    return self.balance(node)

  # Main method to restore balance after stress mode
  def restore_balance(self) -> None:
    # Turn off stress mode immediately
    self.stress_mode = False

    # Verifies that the tree exists
    if self.root is None:
      return

    # Starts the traversal from the bottom and returns the balanced new root
    self.root = self._restore_node(self.root)

    # Cuts off father relation for root
    if self.root is not None:
      self.root.father = None

  # Recursive method to restore the tree's balance bottom-up
  def _restore_node(self, current_node: Node | None) -> Node | None:
    if current_node is None:
      return None

    # Step A: Restore children subtrees first (Post-order: Left and Right)
    current_node.left_son = self._restore_node(current_node.left_son)
    if current_node.left_son is not None:
      current_node.left_son.father = current_node

    current_node.right_son = self._restore_node(current_node.right_son)
    if current_node.right_son is not None:
      current_node.right_son.father = current_node

    # Step B: Update the current node's height with updated children heights
    current_node.update_height()

    # Step C: Resolve imbalances (handles balance factors greater than 1 in magnitude)
    while abs(current_node.balance_factor()) > 1:
      current_node = self.balance(current_node)
      current_node.update_height()

    return current_node

  # Protected method to delete a node and balance the ancestor path
  def _delete_helper(self, current: Node | None, key: tuple[int, float, int]) -> Node | None:
    node = super()._delete_helper(current, key)
    # Check if the node exists
    if node is None:
      return None
    
    # If the node exists, update its height
    node.update_height()
    
    # If stress mode is active, postpone rotations (keep only BST order)
    if self.__stress_mode:
      return node

    # In normal mode, balance node-by-node
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
        if self.__on_rotation:
          self.__on_rotation(case="LR")
        node.left_son = self.left_rotation(node.left_son)
        return self.right_rotation(node)
      # Left-Left (LL) Case: single right rotation
      else:
        if self.__on_rotation:
          self.__on_rotation(case="LL")
        return self.right_rotation(node)

    # Check Right-Heavy cases (bf < -1)
    if bf < -1:
      # Right-Left (RL) Case: child is left-heavy
      if node.right_son and node.right_son.balance_factor() > 0:
        if self.__on_rotation:
          self.__on_rotation(case="RL")
        node.right_son = self.right_rotation(node.right_son)
        return self.left_rotation(node)
      # Right-Right (RR) Case: single left rotation
      else:
        if self.__on_rotation:
          self.__on_rotation(case="RR")
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

    # Notify elemental right turn
    if self.__on_rotation:
      self.__on_rotation(turn="right")

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

    # Notify elemental left turn
    if self.__on_rotation:
      self.__on_rotation(turn="left")

    # Return new subtree root
    return new_root
