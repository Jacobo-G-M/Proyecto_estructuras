class Metrics:

    def __init__(self, observatory) -> None:
        self._observatory = observatory
        self._corrections_accepted: int = 0
        self._discarded_reports: int = 0
        self._conflicts: int = 0
        self._active_events: int = 0
        self._removed_events: int = 0
        self._archived_events: int = 0

    # GETTER for _corrections_accepted
    @property
    def corrections_accepted(self) -> int:
        return self._corrections_accepted

    # SETTER for _corrections_accepted
    @corrections_accepted.setter
    def corrections_accepted(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._corrections_accepted = value
        else:
            raise ValueError("corrections_accepted must be a non-negative integer.")

    # GETTER for _discarded_reports
    @property
    def discarded_reports(self) -> int:
        return self._discarded_reports

    # SETTER for _discarded_reports
    @discarded_reports.setter
    def discarded_reports(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._discarded_reports = value
        else:
            raise ValueError("discarded_reports must be a non-negative integer.")

    # GETTER for _conflicts
    @property
    def conflicts(self) -> int:
        return self._conflicts

    # SETTER for _conflicts
    @conflicts.setter
    def conflicts(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._conflicts = value
        else:
            raise ValueError("conflicts must be a non-negative integer.")

    # GETTER for _active_events
    @property
    def active_events(self) -> int:
        return self._active_events

    # SETTER for _active_events
    @active_events.setter
    def active_events(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._active_events = value
        else:
            raise ValueError("active_events must be a non-negative integer.")

    # GETTER for _removed_events
    @property
    def removed_events(self) -> int:
        return self._removed_events

    # SETTER for _removed_events
    @removed_events.setter
    def removed_events(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._removed_events = value
        else:
            raise ValueError("removed_events must be a non-negative integer.")

    # GETTER for _archived_events
    @property
    def archived_events(self) -> int:
        return self._archived_events

    # SETTER for _archived_events
    @archived_events.setter
    def archived_events(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._archived_events = value
        else:
            raise ValueError("archived_events must be a non-negative integer.")

    # GETTER for observatory
    @property
    def observatory(self):
        return self._observatory

    # SETTER for observatory
    @observatory.setter
    def observatory(self, value) -> None:
        self._observatory = value

    # --- Methods ---



    # Method to count active events pending review
    def pending_events(self, nodes: list) -> int:
        if not nodes:
            return 0
        return sum(
            1 for node in nodes if
            node.event and
            str(node.event.attention_state).strip().lower() in ("pending", "pendiente")
        )

    # Method to count active events already reviewed
    def reviewed_events(self, nodes: list) -> int:
        if not nodes:
            return 0
        return sum(
            1 for node in nodes if
            node.event and
            str(node.event.attention_state).strip().lower() in ("reviewed", "revisado")
        )

    # Method for a dictionary with the counts of the events depending on the priority
    def events_by_priority(self) -> dict[int, int]:
        counts = {3: 0, 2: 0, 1: 0}

        if self._observatory is None:
            return counts

        tree = self._observatory.tree
        if isinstance(tree, list):
            tree = tree[0] if len(tree) > 0 else None

        if tree is not None and hasattr(tree, "width"):
            active_nodes = tree.width()
            for node in active_nodes:
                priority = node.get_key()[0]
                if priority in counts:
                    counts[priority] += 1
                else:
                    counts[priority] = 1
        return counts