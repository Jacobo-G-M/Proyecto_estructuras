try:
    from ...Models.action import Action
except (ImportError, ValueError):
    try:
        from Models.action import Action
    except ImportError:
        try:
            from action import Action
        except ImportError:
            pass

class Undo_stack:
    def __init__(self) -> None:
        self._actions: list[Action] = []

    # GETTER para _actions
    @property
    def actions(self) -> list[Action]:
        return self._actions

    # SETTER para _actions
    @actions.setter
    def actions(self, new_actions: list[Action]) -> None:
        if isinstance(new_actions, list):
            self._actions = new_actions
        else:
            raise TypeError("The 'actions' attribute must be a list.")

    def _is_valid_action(self, action: Action) -> bool:
        return type(action).__name__ == 'Action'

    def stack(self, action: Action) -> None:
        if self._is_valid_action(action):
            self._actions.append(action)
            print("Action successfully pushed to the undo stack.")
        else:
            raise TypeError("Error: The inserted object is not of class Action.")

    def unstack(self) -> Action:
        if not self.is_empty():
            return self._actions.pop()
        else:
            raise IndexError("Error: Cannot pop from an empty undo stack.")

    def is_empty(self) -> bool:
        return len(self._actions) == 0

    def size(self) -> int:
        return len(self._actions)

    def clear(self) -> None:
        self._actions.clear()