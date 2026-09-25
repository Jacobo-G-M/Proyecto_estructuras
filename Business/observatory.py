from __future__ import annotations
from datetime import datetime

class Observatory:
    def __init__(self) -> None:
        self.clock_simulation = datetime.now()
        self.limit = 3
        self.max_time = 0.0
        self.distance_epicenter = 0.0
        self.max_tree_age = 0
        self.stress_mode = False
        
        # 1:1 Relationships
        self.historic = None
        self.report_queue = None
        self.undo_stack = None
        self.metrics = Metrics(self)
        self.geographical_map = None

        # 1:N Relationships 
        self.stations = []
        self.associations = []
        self.tree= []

    # Getter of clock_simulation attribute
    @property
    def clock_simulation(self) -> datetime:
        return self._clock_simulation

    # Setter for clock_simulation attribute
    @clock_simulation.setter
    def clock_simulation(self, value: datetime) -> None:
        if isinstance(value, datetime):
            self._clock_simulation = value
        else:
            raise TypeError("Must be a datetime object.")

    # Getter of limit attribute
    @property
    def limit(self) -> int:
        return self._limit

    # Setter for limit attribute
    @limit.setter
    def limit(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._limit = value
        else:
            raise ValueError("Limit must be a non-negative integer.")

    # Getter of max_time attribute
    @property
    def max_time(self) -> float:
        return self._max_time

    # Setter for max_time attribute
    @max_time.setter
    def max_time(self, value: float) -> None:
        if isinstance(value, (int, float)) and value >= 0:
            self._max_time = float(value)
        else:
            raise ValueError("Max time must be a non-negative number.")

    # Getter of distance_epicenter attribute
    @property
    def distance_epicenter(self) -> float:
        return self._distance_epicenter

    # Setter for distance_epicenter attribute
    @distance_epicenter.setter
    def distance_epicenter(self, value: float) -> None:
        if isinstance(value, (int, float)) and value >= 0:
            self._distance_epicenter = float(value)
        else:
            raise ValueError("Distance must be a non-negative number.")

    # Getter of max_tree_age attribute
    @property
    def max_tree_age(self) -> int:
        return self._max_tree_age

    # Setter for max_tree_age attribute
    @max_tree_age.setter
    def max_tree_age(self, value: int) -> None:
        if isinstance(value, int) and value >= 0:
            self._max_tree_age = value
        else:
            raise ValueError("Max tree age must be a non-negative integer.")

    # Getter of stress_mode attribute
    @property
    def stress_mode(self) -> bool:
        return self._stress_mode

    # Setter for stress_mode attribute
    @stress_mode.setter
    def stress_mode(self, value: bool) -> None:
        if isinstance(value, bool):
            self._stress_mode = value
        else:
            raise TypeError("Stress mode must be a boolean.")


    # --- 1:1 Relationships Getters & Setters ---

    # Getter of historic attribute
    @property
    def historic(self) -> Historic :
        return self._historic

    # Setter for historic attribute
    @historic.setter
    def historic(self, value) -> None:
        if value is None or type(value).__name__ == "Historic":
            self._historic = value
        else:
            raise TypeError("Historic attribute must be of type Historic.")

    # Getter of report_queue attribute
    @property
    def report_queue(self) -> Report_queue:
        return self._report_queue

    # Setter for report_queue attribute
    @report_queue.setter
    def report_queue(self, value) -> None:
        if value is None or type(value).__name__ in ("Report_queue", "Report_Queue"):
            self._report_queue = value
        else:
            raise TypeError("Must be of type Report_queue.")

    # Getter of undo_stack attribute
    @property
    def undo_stack(self) -> Undo_stack:
        return self._undo_stack

    # Setter for undo_stack attribute
    @undo_stack.setter
    def undo_stack(self, value) -> None:
        if value is None or type(value).__name__ in ("Undo_stack", "Undo_Stack"):
            self._undo_stack = value
        else:
            raise TypeError("Must be of type Undo_stack.")

    # Getter of metrics attribute
    @property
    def metrics(self) -> Metrics:
        return self._metrics

    # Setter for metrics attribute
    @metrics.setter
    def metrics(self, value) -> None:
        if value is None or type(value).__name__ == "Metrics":
            self._metrics = value
        else:
            raise TypeError("Must be of type Metrics.")

    # Getter of geographical_map attribute
    @property
    def geographical_map(self) -> Geographical_map:
        return self._geographical_map

    # Setter for geographical_map attribute
    @geographical_map.setter
    def geographical_map(self, value) -> None:
        if value is None or type(value).__name__ in ("Geographical_map", "Geographical_Map"):
            self._geographical_map = value
        else:
            raise TypeError("Must be of type Geographical_map.")

    # --- 1:N Relationships Getters & Setters ---

    # Getter of stations attribute
    @property
    def stations(self) -> list[Station]:
        return self._stations

    # Setter for stations attribute
    @stations.setter
    def stations(self, value: list[Station]) -> None:
        if isinstance(value, list):
            self._stations = value
        else:
            raise TypeError("Stations must be a list.")

    # Getter of associations attribute
    @property
    def associations(self) -> list[Association]:
        return self._associations

    # Setter for associations attribute
    @associations.setter
    def associations(self, value: list[Association]) -> None:
        if isinstance(value, list):
            self._associations = value
        else:
            raise TypeError("Associations must be a list.")

    # --- Methods defined in the class diagram (Empty for now) ---

    def create_event(self) -> None:
        pass

    def process_report(self) -> None:
        pass

    def edit_event(self) -> None:
        pass

    def remove_event(self) -> None:
        pass

    def archive_event(self) -> None:
        pass

    def archive_subtree(self) -> None:
        pass

    def update_clock(self) -> None:
        pass

    def undo_action(self) -> None:
        pass

    def get_costly_access(self) -> list[int]:
        pass