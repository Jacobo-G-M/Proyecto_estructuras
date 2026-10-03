from Models.node import Node
from Business.Structures.tree import Tree

class BST(Tree):
# ------------------------
#       CONSTRUCTOR
# ------------------------
  def __init__(self, id):
    super().__init__(id)
  # Logic applied in BST class
  def _post_process(self, node: Node) -> Node:
    node.update_height()
    return node