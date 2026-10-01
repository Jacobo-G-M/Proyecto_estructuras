import math
from datetime import datetime, timedelta
from Business.historic import Historic
from Business.Structures.report_queue import Report_Queue
from Business.Structures.undo_stack import Undo_stack
from Business.Rules.metrics import Metrics
from Business.geographical_map import Geographical_map
from Models.station import Station
from Business.Rules.asociation import Association
from Business.Rules.sub_tree_archiver import SubtreeArchiver
from Business.Rules.queries import Queries
from Business.scenario_persistence import ScenarioPersistence
from Business.Structures.tree import Tree
from Business.Structures.avl import AVL
from Models.event import Event
from Models.report import Report
from Models.node import Node
import Business.version as Version


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
		self.metrics = Metrics()
		self.geographical_map = None

		# 1:N Relationships
		self.stations = []
		self.associations = []
		self.tree: Tree = AVL(id=1, on_rotation=self._handle_tree_rotation)
		# Auxiliary dictionary for O(1) access to events by ID
		self._events_dict: dict[int, Event] = {}

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
    		if hasattr(self, 'events_dict'):
        		self.update_associations()
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
			if hasattr(self, 'events_dict'):
        		self.update_associations()
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
	
	@property
	def events_dict(self) -> dict[int, Event]:
		return self._events_dict

	@events_dict.setter
	def events_dict(self, value: dict[int, Event]) -> None:
		if isinstance(value, dict):
			self._events_dict = value
		else:
			raise TypeError("events_dict must be a dictionary.")

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
		self.events_dict[event_id] = new_event
		# If self.tree is an AVL instance, insert into it
		if hasattr(self, 'tree') and self.tree is not None:
			if hasattr(self.tree, 'insert'):
				self.tree.insert(new_node)
		# -----------------------------------------------------------------
		# 5. REGISTER STATION AND UNDO ACTION
		# -----------------------------------------------------------------
		# If station is provided, register initial report/station acceptance
		# (e.g., station.my_reports.append(...) or add to event accepted stations)

		# TODO: Record action in self.undo_stack to allow undoing this creation
		self.update_associations()

		print(f"Event {event_id} successfully created with priority {priority}.")
		return new_event

	# Callback handler to register AVL rotations into Metrics
	def _handle_tree_rotation(self, case: str | None = None, turn: str | None = None) -> None:
		if self.metrics is None:
			return
		if case:
			self.metrics.register_case(case)
		if turn:
			self.metrics.register_turn(turn)

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

	#method to process all report_queue reports -------------------------------------------------
	def process_report(self) -> None:
		"""
		Processes reports from the queue
		"""

		#checks if the queue is empty
		if self.report_queue is None or self.report_queue.is_empty():
			print("No reports in the queue to process.")
			return

		#unqueue all reports one by one from report_queue
		while not self.report_queue.is_empty():
			report = self.report_queue.dequeue()

			# Check if the report ID corresponds to a permanently deleted event
			#it discards a report from an event that was previously delted
			if self.historic is not None and report.id in self.historic.deleted:
				print(f"Report ID {report.id} discarded: Event was previously deleted.")
				if self.metrics is not None:
					self.metrics.discarded_reports += 1
				continue

			event, is_archived = self._find_event(report.id)
			self._apply_report_rules(report, event, is_archived)

	#method to check if the event is active or is archived
	def _find_event(self, event_id: int) -> tuple[Event | None, bool]:
		"""
		Locates an event by ID across active and archived catalogs.
		Returns a tuple (Event, is_archived).
		"""
		if event_id in self.events_dict:
			return self.events_dict[event_id], False

		if self.historic is not None and event_id in self.historic.archived:
			return self.historic.archived[event_id], True

		return None, False

	#ckecks if a report and an event has the same information
	def _has_same_physical_data(self, report: Report, event: Event) -> bool:
		"""
		Checks if physical parameters (magnitude, depth, epicenter, date_time)
		match between a report and an event (rounded to 1 decimal place).
		"""
		rep_mag = round(report.magnitude, 1)
		ev_mag = round(event.magnitude, 1)
		rep_depth = round(report.depth, 1)
		ev_depth = round(event.depth, 1)
		rep_epi = (round(report.epicenter[0], 1), round(report.epicenter[1], 1))
		ev_epi = (round(event.epicenter[0], 1), round(event.epicenter[1], 1))

		return (
			rep_mag == ev_mag and
			rep_depth == ev_depth and
			rep_epi == ev_epi and
			report.date_time == event.date_time
		)

	#method that compares revision ids
	def _apply_report_rules(self, report: Report, event: Event | None, is_archived: bool) -> None:
		"""
		Applies the 5 comparison rules between an incoming report and an existing event.
		"""
		# Rule 1: Unknown ID -> Create new active event
		#if its not an archived or deleted event, event is None, so its a new event
		if event is None:
			#gets the station that gender the report or None to give him one
			station = report.origin_station[0] if report.origin_station else None
			created_event = self.create_event(
				event_id=report.id,
				magnitude=report.magnitude,
				depth=report.depth,
				epicenter=report.epicenter,
				date_time=report.date_time,
				station=station
			)
			if created_event is not None:
				# A new event can enter with review >= 1
				#updates the review to match with the report
				created_event.review = report.review
				# Register origin stations from report to the new event
				if report.origin_station:
					for st in report.origin_station:
						created_event.add_origin_station(st)
			return

		# Rule 2: Higher revision -> Accepted correction
		if report.review > event.review:
			# If the event was archived, reactivate it into the active catalog
			if is_archived and self.historic is not None:
				reactivated = self.historic.unarchive_event(event.id)
				if reactivated is not None:
					#adds to active events
					self.events_dict[reactivated.id] = reactivated
					#inserts again to tree
					if hasattr(self, 'tree') and self.tree is not None:
						new_node = Node(id=reactivated.id, event=reactivated)
						self.tree.insert(new_node)
					event = reactivated

			#edits the event with the new information
			self.edit_event(
				event_id=event.id,
				new_magnitude=report.magnitude,
				new_depth=report.depth,
				new_epicenter=report.epicenter,
				new_date_time=report.date_time
			)
			# Update to the report's revision
			event.review = report.review
			if self.metrics is not None:
				self.metrics.corrections_accepted += 1
			print(f"Correction accepted for Event {event.id}. Updated to review {event.review}.")
			return

		# Rule 3 & 4: Same revision
		if report.review == event.review:
			if self._has_same_physical_data(report, event):
				# Rule 3: Confirmation -> Add origin stations
				#add stations from report to the stations of the event
				if report.origin_station:
					for st in report.origin_station:
						event.add_origin_station(st)
				print(f"Report confirmed for Event {event.id}. Station(s) registered.")
			else:
				# Rule 4: Conflict -> Reject report, don't modify event
				if self.metrics is not None:
					self.metrics.conflicts += 1
				print(f"Conflict detected for Event {event.id} at review {report.review}. Report rejected.")
			return

		# Rule 5: Lower revision -> Discard old report
		if report.review < event.review:
			if self.metrics is not None:
				self.metrics.discarded_reports += 1
			print(f"Report discarded for Event {event.id}: Review {report.review} is older than current {event.review}.")
			return

	#general method to calculate priority --------------------------------------------------------------------------------------------
	def calculate_priority(self, magnitude: float, depth: float, epicenter: tuple[float, float]) -> int:
		"""
		3 (High): M ≥ 6.0, or (M ≥ 4.5 and H ≤ 30.0 km in a populated area)
		2 (Medium): M ≥ 4.5 (and does not meet the criteria for High)
		1 (Low): Does not meet any of the above criteria
		"""
		x, y = epicenter
		is_populated = False
		
		if self.geographical_map is not None:
			is_populated = self.geographical_map.is_in_populated_zone(x, y)

		# Priority 3 (High)
		if magnitude >= 6.0 or (magnitude >= 4.5 and depth <= 30.0 and is_populated):
			return 3
			
		# Priority 2 (Medium)
		elif magnitude >= 4.5:
			return 2
			
		# Priority 1 (Low)
		else:
			return 1

	def edit_event(
		self,
		event_id: int,
		new_magnitude: float,
		new_depth: float,
		new_epicenter: tuple[float, float],
		new_date_time: datetime
	) -> Event | None:
		if event_id not in self.events_dict:
			print(f"Error: Event ID {event_id} no se encuentra en el catálogo activo.")
			return None

		event_to_edit = self.events_dict[event_id]

		if not (-2.0 <= new_magnitude <= 10.0):
			print("Error: La magnitud debe estar entre -2.0 y 10.0.")
			return None
		if not (0.0 <= new_depth <= 700.0):
			print("Error: La profundidad debe estar entre 0.0 y 700.0 km.")
			return None
		if new_date_time > self.clock_simulation:
			print("Error: El tiempo de ocurrencia no puede ser futuro.")
			return None

		# Calculate the new priority
		old_priority = event_to_edit.priority
		old_magnitude = event_to_edit.magnitude
		new_priority = self.calculate_priority(new_magnitude, new_depth, new_epicenter)

		# Check whether the key K = (P, M, I) will change
		key_changed = (old_priority != new_priority) or (old_magnitude != new_magnitude)

		if key_changed and self.tree is not None:
			deleted_node = self.tree.delete(event_to_edit.get_key())

		# Updating Event Attributes
		event_to_edit.magnitude = round(new_magnitude, 1)
		event_to_edit.depth = round(new_depth, 1)
		event_to_edit.epicenter = new_epicenter
		event_to_edit.date_time = new_date_time
		event_to_edit.priority = new_priority
		event_to_edit.attention_state = "Pending"
		event_to_edit.review += 1

		# Reinsert into the tree if the key has changed
		if key_changed and self.tree is not None:
			updated_node = Node(id=event_id, event=event_to_edit)
			self.tree.insert(updated_node)
		self.update_associations()
		print(f"Event {event_id} corregido. Clave actualizada: {key_changed}.")
		return event_to_edit

	def remove_event(self, event_id: int) -> None:
		# Validation: Check if the event exists in the active catalog
		if not hasattr(self, 'events_dict') or event_id not in self.events_dict:
			print(f"Error: El evento {event_id} no se encuentra en el catálogo activo.")
			return None

		event_to_remove = self.events_dict[event_id]

		print(f"Preparando para eliminar el evento activo: ID={event_id}, K=(P:{event_to_remove.priority}, M:{event_to_remove.magnitude})")

		# Remove from the tree if it exists
		if hasattr(self, 'tree') and self.tree is not None:
			self.tree.delete(event_to_remove.get_key())

		del self.events_dict[event_id]

		if self.historic is not None:
			self.historic.delete_event(event_to_remove)

		self.update_associations()
		# Update metrics if applicable
		if self.metrics is not None:
			self.metrics.active_events -= 1

		# TODO: Registrar acción completa en undo_stack (Deep Copy)

		print(f"Eliminación completada: El identificador {event_id} ha sido retirado del catálogo.")
		return event_to_remove

	def archive_subtree(self) -> None:
		if self.tree is None or self.tree.root is None:
			print("El catálogo activo está vacío. No hay nada que archivar.")
			return

		# Search for the best branch to archive based on the defined rules
		best_root_node, nodes_to_archive = self._find_best_branch()

		if not nodes_to_archive:
			print("No existe ninguna rama que cumpla los criterios para ser archivada.")
			return

		ids_afectados = [n.id for n in nodes_to_archive]
		print(f"Archivando subárbol con raíz ID={best_root_node.id}.")
		print(f"Eventos afectados ({len(ids_afectados)}): {ids_afectados}")
		print(f"Justificación: Todos los eventos tienen P=1 y antigüedad > {self.max_tree_age} horas.")

		# extract the events from the nodes and archive them
		for node in nodes_to_archive:
			event_id = node.id
			
			if event_id in self.events_dict:
				event_to_archive = self.events_dict[event_id]
				
				self.tree.delete(event_to_archive.get_key())
				
				del self.events_dict[event_id]
				
				if self.historic is not None:
					self.historic.archive_event(event_to_archive)

		if self.metrics is not None:
			self.metrics.active_events -= len(nodes_to_archive)

		print("Archivo masivo ejecutado con éxito.")

	# --- MÉTODOS AUXILIARES PARA EL ARCHIVO MASIVO ---

	def _find_best_branch(self) -> tuple:
		"""
		Traverse the tree to find the branch that meets the strict rules.
		Delegates evaluation and tie-breaking to SubtreeArchiver.
		"""
		return SubtreeArchiver.find_best_branch(
			tree=self.tree,
			max_age_hours=self.max_tree_age,
			simulation_clock=self.clock_simulation
		)

	# Public method: it checks first if there is a existing tree, then executes the
	# method in tree
	def _get_all_nodes_with_depth(self, current_node = None, current_depth: int = 0) -> list[tuple]:
		if self.tree is None:
			return []
		return self.tree.get_all_nodes_with_depth(current_node, current_depth)

	def update_clock(self, new_time: datetime | None = None, hours: float = 0.0) -> datetime | None:
		"""
		Advances the simulation clock according to project Section 3 and Section 13.
		- new_time: Specific future datetime to advance the clock to.
		- hours: Optional increment in hours to advance relative to current clock.
		Validates that time only moves forward and constitutes an undoable action.
		"""
		if new_time is None:
			if hours <= 0:
				print("Error: You must provide a valid future datetime or a positive number of hours.")
				return None
			target_time = self.clock_simulation + timedelta(hours=hours)
		else:
			target_time = new_time

		if not isinstance(target_time, datetime):
			print("Error: Target time must be an instance of datetime.")
			return None

		if target_time <= self.clock_simulation:
			print(f"Error: The clock can only advance to a future time. Current: {self.clock_simulation.isoformat()}, Target: {target_time.isoformat()}")
			return None

		# Save previous time for undo/traceability
		previous_time = self.clock_simulation
		self.clock_simulation = target_time

		print(f"Clock advanced successfully: {previous_time.isoformat()} -> {self.clock_simulation.isoformat()}")
		return self.clock_simulation

	def undo_action(self) -> None:
		pass

	# Method to identify high-priority events whose node depth exceeds limit L
	def get_costly_access(self) -> list[int]:
		"""
		Returns a list of IDs of high-priority events (priority = 3)
		whose depth in the active AVL tree is strictly greater than limit L.
		"""
		if self.tree is None or self.tree.root is None:
			return []

		costly_ids: list[int] = []
		all_nodes_with_depth = self._get_all_nodes_with_depth(self.tree.root, 0)

		for node, depth in all_nodes_with_depth:
			if node.event is not None and node.event.priority == 3 and depth > self.limit:
				costly_ids.append(node.id)

		return costly_ids

	# ------------------------
	# Section 11 Queries Facade Delegation Methods
	# ------------------------
	def query_top_k_pending(self, k: int) -> tuple[list[Event], int]:
		"""Delegates to Queries.top_k_pending."""
		return Queries.top_k_pending(self.tree, k)

	def query_events_by_filters(
		self,
		min_mag: float | None = None,
		max_mag: float | None = None,
		max_depth: float | None = None,
		start_date: datetime | None = None,
		end_date: datetime | None = None
	) -> tuple[list[Event], int]:
		"""Delegates to Queries.events_by_filters."""
		return Queries.events_by_filters(self.tree, min_mag, max_mag, max_depth, start_date, end_date)

	def query_event_associations(
		self,
		event_id: int,
		max_time_hours: float | None = None,
		max_distance_km: float | None = None
	) -> tuple[dict, int]:
		"""Delegates to Queries.event_associations."""
		max_t = max_time_hours if max_time_hours is not None else self.max_time
		max_d = max_distance_km if max_distance_km is not None else self.distance_epicenter
		return Queries.event_associations(self.tree, self.historic, self.associations, event_id, max_t, max_d)

	def query_costly_high_priority_events(self) -> tuple[list[dict], int]:
		"""Delegates to Queries.costly_high_priority_events."""
		return Queries.costly_high_priority_events(self.tree, self.limit)

	def save_scenario(self, filepath: str) -> None:
		"""Delegates full structural scenario export to ScenarioPersistence."""
		ScenarioPersistence.export_to_json(self, filepath)

	def load_scenario_by_topology(self, filepath: str, stress_mode_override: bool | None = None) -> tuple[bool, list[str]]:
		"""Delegates atomic topology load and validation to ScenarioPersistence."""
		return ScenarioPersistence.load_by_topology(self, filepath, stress_mode_override)

	def load_scenario_by_insertions(self, filepath: str, adopt_avl: bool = False) -> dict:
		"""Delegates sequential insertion comparison to ScenarioPersistence."""
		result = ScenarioPersistence.load_by_insertions(filepath, self.geographical_map)
		if adopt_avl and result.get("avl") is not None:
			self.tree = result["avl"]
			self.events_dict = {ev.id: ev for ev in result.get("events", [])}
		return result
        print(f"Error: El identificador {event_id} no existe en ningún catálogo.")
        return None
	
	def query_event(self, event_id: int) -> dict | None:
        # 1. Search in the Active Catalog
        if hasattr(self, 'events_dict') and event_id in self.events_dict:
            event = self.events_dict[event_id]
            
            # Obtain node metrics (depth, height, balance factor) from the AVL tree
            node_metrics = self._get_node_metrics(event_id)
            
            # Check if the epicenter is in a populated zone
            is_populated = False
            if getattr(self, 'geographical_map', None) is not None:
                is_populated = self.geographical_map.is_in_populated_zone(event.epicenter[0], event.epicenter[1])

            return {
                "id": event.id,
                "status": "Active",
                "current_data": {
                    "magnitude": event.magnitude,
                    "depth": event.depth,
                    "epicenter": event.epicenter,
                    "date_time": event.date_time
                },
				"priority": event.priority,
                "review": event.review,
                "stations": getattr(event, "stations", []),
                "is_in_populated_zone": is_populated,
                "key_K": (event.priority, event.magnitude, event.id),
                "attention_state": event.attention_state,
                "node_depth": node_metrics.get("depth", 0),
                "height": node_metrics.get("height", 0),
                "balance_factor": node_metrics.get("balance_factor", 0),
                #"associations": self._get_event_associations(event_id) PENDING: Implement association retrieval if needed
            }

        # 2. Search in the Historical Catalog (Archived or Deleted)
        if getattr(self, 'historic', None) is not None:
            if hasattr(self.historic, 'archived') and event_id in self.historic.archived:
                event = self.historic.archived[event_id]
                return {"id": event_id, "status": "Archived", "event_data": event}
            
            if hasattr(self.historic, 'deleted') and event_id in self.historic.deleted:
                event = self.historic.deleted[event_id]
                return {"id": event_id, "status": "Deleted", "event_data": event}

        print(f"Error: El identificador {event_id} no existe en ningún catálogo.")

	def _get_node_metrics(self, event_id: int) -> dict:
        """
		Retrieves the depth, height, and balance factor of the node corresponding to the given event_id in the AVL tree.
        """
    	if event_id not in self.events_dict or self.tree is None:
            return {"depth": 0, "height": 0, "balance_factor": 0}
            
        event = self.events_dict[event_id]

        search_key = event.get_key()
        
        return self.tree.get_node_metrics(search_key)
	def verify_structure(self) -> list[str]:
        """
        Audits the structure of the active catalog.
        Returns a list of errors or inconsistencies found.
        """
        reporte = []
        
        if self.tree is None or getattr(self.tree, 'root', None) is None:
            return ["Auditoría: El árbol activo está vacío."]

        ids_visitados = set()
        # Use a mutable dictionary or list to maintain the state of the previous node during recursion
        estado_auditoria = {"clave_previa": None}

    	def auditar_nodo(nodo) -> int:
            """
            Recursive function that traverses the tree in in-order.
            Returns the recalculated height of the node.
            """
            # Rule: Height of an empty tree is -1
            if nodo is None:
                return -1

            # 1. Audit left subtree
            altura_izq = auditar_nodo(nodo.left_son)

            # 2. Verify uniqueness and references (cycles)
            if nodo.id in ids_visitados:
                reporte.append(f"Error Crítico: Identificador duplicado o ciclo de punteros detectado en ID {nodo.id}.")
            else:
                ids_visitados.add(nodo.id)

            # 3. Verify global lexicographical order K=(P, M, I) via in-order traversal
            clave_actual = nodo.get_key()
            if estado_auditoria["clave_previa"] is not None:
                if clave_actual <= estado_auditoria["clave_previa"]:
                    reporte.append(f"Error de Orden: El nodo {clave_actual} es menor o igual a su predecesor {estado_auditoria['clave_previa']}.")
            estado_auditoria["clave_previa"] = clave_actual

            # 4. Audit right subtree
            altura_der = auditar_nodo(nodo.right_son)

            # 5. Recalculate and verify heights
            # Rule: Actual height = 1 + max(left_height, right_height)
            altura_real = 1 + max(altura_izq, altura_der)
            if nodo.height != altura_real:
                reporte.append(f"Error de Metadatos (ID {nodo.id}): Altura guardada={nodo.height}, Altura real={altura_real}.")

            # 6. Calculate and verify balance factor
            # Rule: Balance factor = left_height - right_height
            factor_calculado = altura_izq - altura_der
            
            if not self.stress_mode:
                # In normal mode, the balance factor must strictly be in {-1, 0, 1}
                if factor_calculado not in (-1, 0, 1):
                    reporte.append(f"Error de Balance (Modo Normal): ID {nodo.id} tiene un factor de {factor_calculado}.")
            else:
                # In stress mode, imbalance is allowed but should be reported
                if factor_calculado not in (-1, 0, 1):
                    reporte.append(f"Aviso (Modo Estrés): Desbalance esperado en ID {nodo.id} con factor {factor_calculado}.")

            return altura_real

        # Start traversal from the root
        auditar_nodo(self.tree.root)

        # 7. Cross-check with auxiliary O(1) structure
        if hasattr(self, 'events_dict'):
            if len(ids_visitados) != len(self.events_dict):
                reporte.append(f"Error de Integridad: El árbol tiene {len(ids_visitados)} nodos, pero el diccionario activo tiene {len(self.events_dict)}.")

        if not reporte:
            reporte.append("Auditoría Exitosa: El árbol cumple todas las propiedades matemáticas de estructura y orden.")

        return reporte
	# ---------------------------------------------------------
	# ASSOCIATION LOGIC (REPLICAS AND REFERENCES)
	# ---------------------------------------------------------

	def update_associations(self) -> None:
		"""
		Recalculates all associations in the system.
		Must be called upon completion of create_event, edit_event, remove_event, or when changing max_time / distance_epicenter.
		"""
		# 1. Clear current associations
		self.associations = []
		
		# 2. Retrieve all valid events (Active and Archived, excluding Deleted)
		valid_events = self._get_valid_events_for_associations()
		
		if not valid_events:
			return

		# Temporary dictionary to build associations (Key: Parent ID)
		assoc_dict: dict[int, Association] = {}

		# 3. Evaluate each event to find its best parent (reference)
		for child in valid_events:
			best_parent = self._find_best_candidate(child, valid_events)
			
			if best_parent is not None:
				# If the parent does not have an association created yet, create it
				if best_parent.id not in assoc_dict:
					assoc_dict[best_parent.id] = Association(assoc_id=best_parent.id, chosen_reference=best_parent)
				
				# Add the child to the parent's list of replicas
				# Internal print of add_replica can be silenced if many, or kept for traceability
				assoc_dict[best_parent.id].add_replica(child)

		# 4. Save the resulting associations in the official list
		self.associations = list(assoc_dict.values())
		print(f"Asociaciones actualizadas: {len(self.associations)} eventos de referencia detectados.")

	def _get_valid_events_for_associations(self) -> list[Event]:
		"""
		Returns a flat list with all active and archived events.
		Deleted events are excluded according to business rules.
		"""
		events = list(self.events_dict.values())
		
		if self.historic is not None and hasattr(self.historic, 'archived'):
			events.extend(self.historic.archived.values())
			
		return events

	def _find_best_candidate(self, child: Event, valid_events: list[Event]) -> Event | None:
		"""
		Finds the best reference event for a given child event.
		Applies restrictive rules and a deterministic tie-breaking criterion.
		"""
		best_parent = None
		# Tuple to store the minimum score: (distance, time_difference, -magnitude, -id)
		best_score = None

		for parent in valid_events:
			# Avoid comparing an event with itself
			if parent.id == child.id:
				continue

			# Instantiate a temporary association to leverage the existing validation method
			temp_assoc = Association(assoc_id=parent.id, chosen_reference=parent)
			
			if temp_assoc.verify_association(child, self.max_time, self.distance_epicenter):
				# If it passes strict verification (M_parent > M_child, valid time and distance)
				# Compute exact values for deterministic tie-breaking
				time_diff = (child.date_time - parent.date_time).total_seconds() / 3600.0
				dx = parent.epicenter[0] - child.epicenter[0]
				dy = parent.epicenter[1] - child.epicenter[1]
				distance = math.sqrt(dx**2 + dy**2)

				current_score = (distance, time_diff, -parent.magnitude, -parent.id)

				if best_score is None or current_score < best_score:
					best_score = current_score
					best_parent = parent

		return best_parent

