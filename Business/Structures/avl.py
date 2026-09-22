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
    def _stress_mode(self, value: bool) -> None:
        self.__stress_mode = value
  # ------------------------
  #         METHODS
  # ------------------------
  def balance(self):
    pass
  
  def restore_balance(self):
    pass
  
  def left_rotation(self):
    pass
  
  def right_rotation(self):
    pass