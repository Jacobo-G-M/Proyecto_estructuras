class Action:
    def __init__(self, id: int):
        self.id = id

    # --- id ---
    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("id must be an integer.")
        self._id = value

    def __repr__(self) -> str:
        return f"Action(id={self._id})"