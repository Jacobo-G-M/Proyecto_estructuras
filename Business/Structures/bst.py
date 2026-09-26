from tree import Tree

class BST(Tree):
# ------------------------
#       CONSTRUCTOR
# ------------------------
  def __init__(self, id):
    super().__init__(id)
  # DENTRO DE BST (Hijo de Tree)
def _post_process(self, node: Node) -> Node:
      return node