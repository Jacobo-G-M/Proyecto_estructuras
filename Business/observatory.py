from __future__ import annotations
from datetime import datetime
from Business.historic import Historic
from Business.report_queue import Report_queue
from Business.undo_stack import Undo_stack
from Business.metrics import Metrics
from Business.geographical_map import Geographical_map
from Business.station import Station
from Business.association import Association
import Business.tree as Tree
import Business.event as Event
import Business.Version as Version


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
	def report_queue(self) -> Report_Queue:
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

	# ------------------------
  #         METHODS
  # ------------------------

	# Method to manually create an active event
	def create_event(
		self,
		event_id: int,
		magnitude: float,
		depth: float,
		epicenter: tuple[float, float],
		date_time: datetime,
		station: Station
	) -> Event | None:
		# -----------------------------------------------------------------
		# 1. RANGE AND DATA VALIDATIONS
		# -----------------------------------------------------------------
		if not isinstance(event_id, int) or not (1 <= event_id <= 999999):
			print("Error: Event ID must be an integer between 1 and 999999.")
			return None

		if not (-2.0 <= magnitude <= 10.0):
			print("Error: Magnitude must be between -2.0 and 10.0.")
			return None

		if not (0.0 <= depth <= 700.0):
			print("Error: Depth must be between 0.0 and 700.0 km.")
			return None

		if not (isinstance(epicenter, tuple) and len(epicenter) == 2):
			print("Error: Epicenter must be a tuple of two coordinates (x, y).")
			return None

		x, y = epicenter
		if not (0.0 <= x <= 1000.0 and 0.0 <= y <= 1000.0):
			print("Error: Coordinates x and y must be between 0.0 and 1000.0 km.")
			return None

		if date_time > self.clock_simulation:
			print("Error: Occurrence time cannot be after the simulation clock.")
			return None

		# -----------------------------------------------------------------
		# 2. CHECK ID UNIQUENESS (Active, Archived, or Deleted)
		# -----------------------------------------------------------------
		if self._is_id_registered(event_id):
			print(f"Error: Event ID {event_id} already exists in active, archived, or deleted catalog.")
			return None

		# -----------------------------------------------------------------
		# 3. DERIVE PRIORITY & CREATE EVENT OBJECT
		# -----------------------------------------------------------------
		priority = self.calculate_priority(magnitude, depth, epicenter)

		# TODO: put stations in event
		new_event = Event(
			id=event_id,
			priority=priority,
			magnitude=round(magnitude, 1),
			depth=round(depth, 1),
			epicenter=(round(x, 1), round(y, 1)),
			date_time=date_time,
			review=1,
			attention_state="Pending",
			status="Active"
		)

		# -----------------------------------------------------------------
		# 4. INSERT INTO TREE (AVL)
		# -----------------------------------------------------------------
		new_node = Node(id=event_id, event=new_event)
		
		# If self.tree is an AVL instance, insert into it
		if hasattr(self, 'tree') and self.tree is not None:
			if hasattr(self.tree, 'insert'):
				self.tree.insert(new_node)
		elif hasattr(self, 'avl') and self.avl is not None:
			self.avl.insert(new_node)

		# -----------------------------------------------------------------
		# 5. REGISTER STATION AND UNDO ACTION
		# -----------------------------------------------------------------
		# If station is provided, register initial report/station acceptance
		# (e.g., station.my_reports.append(...) or add to event accepted stations)

		# TODO: Record action in self.undo_stack to allow undoing this creation
		# TODO: Recalculate associations if needed

		print(f"Event {event_id} successfully created with priority {priority}.")
		return new_event

	# Method to verify if an event ID is already taken
	def _is_id_registered(self, event_id: int) -> bool:
		# Check in historic (archived and deleted)
		if self.historic is not None:
			# Check the archived events
			for ev in self.historic.archived:
				if ev.id == event_id:
					return True
			# Check the deleted events
			for ev in self.historic.deleted:
				if ev.id == event_id:
					return True

		# Check in active tree
		if hasattr(self, 'tree') and self.tree is not None:
			for node in self.tree.inorder():
				# Extract the event ID from get_key(): (priority, magnitude, event_id)
				_, _, current_event_id = node.get_key()
				if current_event_id == event_id:
					return True

		return False

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

	def is_in_populated_zone(self, epicenter: tuple[float, float]) -> bool:
		# Check if epicenter exists
		if epicenter is None:
			return False
		# Check if geographical map exists
		if self.geographical_map is None:
			return False
		# Stores the existing zones in zones variable
		zones = self._geographical_map.zones
		# Stores the coordinates in two variables
		x, y = epicenter

		# Iterate every existing zone, checking if is inside or on the border of a zone
		for zone in zones:
			if zone.is_populated and zone.contains(x, y):
				return True
		return False

	def get_costly_access(self) -> list[int]:
		pass