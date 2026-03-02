# tree.py
# Defines the TreeNode class used to build the parse tree.
#
# Every grammar rule that fires creates one TreeNode.
# Leaf nodes hold token values (e.g. "id:x", "num:3").
# Internal nodes hold rule names (e.g. "Expr", "Term").


class TreeNode:
    """
    Represents a single node in the parse tree.

    Attributes:
        label    : str  – name of the grammar rule OR a token value
        children : list – ordered list of child TreeNode objects
    """

    def __init__(self, label: str):
        self.label = label
        self.children: list["TreeNode"] = []

    def add_child(self, node: "TreeNode") -> None:
        """Attach a child node to this node (left-to-right order)."""
        self.children.append(node)

    def is_leaf(self) -> bool:
        """Returns True if this node has no children (it is a terminal)."""
        return len(self.children) == 0

    def __repr__(self) -> str:
        return f"TreeNode({self.label!r}, children={len(self.children)})"
