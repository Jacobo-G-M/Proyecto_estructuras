class Metrics:

    def __init__(self, observatory) -> None:
        self._corrections_accepted: int = 0
        self._discarded_reports: int = 0
        self._observatory = observatory

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

    #GETTER for Observatory
    @property
    def observatory(self):
        return self._observatory


    # --- Methods ---

    def cant_leaves(self) -> int:
        pass

    def conflicts(self) -> int:
        pass

    def case_LL(self) -> int:
        pass

    def case_RR(self) -> int:
        pass

    def case_LR(self) -> int:
        pass

    def case_RL(self) -> int:
        pass

    def pending_events(self) -> int:
        pass

    def reviewed_events(self) -> int:
        pass

    def active_events(self) -> int:
        pass

        #returns the cant of archived events
    def archived_events(self) -> int:
        if self._observatory is not None and self._observatory.historic is not None:
            return len(self._observatory.historic.archived)
        return 0

        #method for a diccionary with the counts of the events depending the priority
    def events_by_priority(self) -> dict[int, int]:
        counts = {3:0, 2:0, 1:0}

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