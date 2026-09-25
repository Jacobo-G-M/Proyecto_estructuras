from __future__ import annotations

try:
    from Models.action import Action
except ImportError:
    from ...Models.action import Action

class Undo_stack:
    def __init__(self) -> None:
        # Internal list to represent the stack of actions
        self._actions: list[Action] = []

    # GETTER for _actions
    @property
    def actions(self) -> list[Action]:
        return self._actions

    # SETTER for _actions
    @actions.setter
    def actions(self, new_actions: list[Action]) -> None:
        if isinstance(new_actions, list):
            self._actions = new_actions
        else:
            raise TypeError("The 'actions' attribute must be a list.")

    # --- Auxiliary and Stack Operations ---

    def _is_valid_action(self, action: Action) -> bool:
        return type(action).__name__ == 'Action'

    def push(self, action: Action) -> None:
        if self._is_valid_action(action):
            self._actions.append(action)
            print("Action successfully pushed to the undo stack.")
        else:
            raise TypeError("Error: The inserted object is not of class Action.")

    def pop(self) -> Action:
        if not self.is_empty():
            return self._actions.pop()
        else:
            raise IndexError("Error: Cannot pop from an empty undo stack.")

    def is_empty(self) -> bool:
        return len(self._actions) == 0

    # ----- methods -----

    #method to get de cant of items on the undo_stack
    def size(self) -> int:
        return len(self._actions)