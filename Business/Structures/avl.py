from tree import Tree

class AVL(Tree):
  # ------------------------
  #       CONSTRUCTOR
  # ------------------------
  def __init__(self, id: int, stress_mode: bool = False):
    super().__init__(id)
    self.__stress_mode: bool = stress_mode
    
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
  def balance(self):
    pass

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

  
  def left_rotation(self):
    pass
  
  def right_rotation(self):
    pass


  