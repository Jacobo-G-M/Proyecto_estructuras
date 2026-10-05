from datetime import datetime

class Action:
    """
    Model representing an action recorded in the Undo Stack (Section 13).
    
    Implements the Memento Pattern by saving a full snapshot
    of the observatory operational state prior to executing a mutation,
    enabling state restoration upon undo operations.
    """
    def __init__(
        self,
        id: int,
        action_type: str = "",
        description: str = "",
        snapshot: dict | None = None,
        timestamp: datetime | None = None
    ):
        # Initialization of attributes via setters for type validation
        self.id = id
        self.action_type = action_type
        self.description = description
        self.snapshot = snapshot if snapshot is not None else {}
        self.timestamp = timestamp if timestamp is not None else datetime.now()

    # --- id: Sequential numeric identifier of the action in the stack ---
    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("id must be an integer.")
        self._id = value

    # --- action_type: Operation type (CREATE_EVENT, EDIT_EVENT, REMOVE_EVENT, etc.) ---
    @property
    def action_type(self) -> str:
        return self._action_type

    @action_type.setter
    def action_type(self, value: str):
        self._action_type = str(value)

    # --- description: Readable textual explanation for the user or the interface ---
    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = str(value)

    # --- snapshot: Dictionary containing the deep previous state of the components ---
    @property
    def snapshot(self) -> dict:
        return self._snapshot

    @snapshot.setter
    def snapshot(self, value: dict):
        if not isinstance(value, dict):
            raise TypeError("snapshot must be a dictionary.")
        self._snapshot = value

    # --- timestamp: Timestamp in which the action was captured ---
    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: datetime):
        self._timestamp = value

    def __repr__(self) -> str:
        if not self._action_type and not self._description:
            return f"Action(id={self._id})"
        return f"Action(id={self._id}, type='{self._action_type}', desc='{self._description}')"