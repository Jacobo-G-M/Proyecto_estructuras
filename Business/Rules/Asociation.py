import math
from Business.Event import Event
from datetime import timedelta
class Association:

    def __init__(self, assoc_id: int, chosen_reference: Event) -> None:
   
        self._id: int = assoc_id
        self._chosen_reference: Event = None

        self._referenced_by: list[Event] = []

    # GETTER for _id
    @property
    def id(self) -> int:
        return self._id
    #SETTER para _id
    @id.setter
    def id(self, new_id: int) -> None:
        if isinstance(new_id, int):
            self._id = new_id
        else:
            raise TypeError("The id must be an integer.")

    # GETTER for _chosen_reference
    @property
    def chosen_reference(self) -> Event:
        return self._chosen_reference
    
    # SETTER for _chosen_reference

    @chosen_reference.setter
    def chosen_reference(self, event: Event) -> None:
        if self._is_valid_event(event):
            self._chosen_reference = event
        else:
            raise TypeError("The reference event must be of class Event.")

    # GETTER for _referenced_by
    @property
    def referenced_by(self) -> list[Event]:
        return self._referenced_by
    
    # SETTER for _referenced_by

    @referenced_by.setter
    def referenced_by(self, new_replicas: list[Event]) -> None:
        if isinstance(new_replicas, list):
            self._referenced_by = new_replicas
        else:
            raise TypeError("The 'referenced_by' attribute must be a list.")

    # --- Auxiliary and Business Methods ---

    def _is_valid_event(self, event: Event) -> bool:
        return type(event).__name__ == 'Event'
    
    def _calculate_distance(self, coord_a: tuple[float, float], coord_b: tuple[float, float]) -> float:
        """Calculate the Euclidean distance between two pairs of coordinates (x, y)."""
        dx = coord_a[0] - coord_b[0]
        dy = coord_a[1] - coord_b[1]
        return math.sqrt(dx**2 + dy**2)

    def verify_association(self, candidate_event: Event, max_time: float, max_distance: float) -> bool:
        parent = self.chosen_reference
        child = candidate_event
        if parent.magnitude <= child.magnitude:
            return False
        if parent.date_time >= child.date_time:
            return False
        time_diff: timedelta = child.date_time - parent.date_time
        time_diff_hours: float = time_diff.total_seconds() / 3600.0
        if time_diff_hours > max_time:
            return False
        distance: float = self._calculate_distance(parent.epicenter, child.epicenter)
        if distance > max_distance:
            return False
        return True

    def add_replica(self, child_event: Event) -> None:
        if self._is_valid_event(child_event):
            self._referenced_by.append(child_event)
            print("Replica added successfully to the reference event.")
        else:
            raise TypeError("The child event must be of class Event.")

    