import copy
import json
import math
import os
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
from Business.version import Version


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
		self.undo_stack = Undo_stack()
		self.metrics = Metrics()
		self.geographical_map = None

		# 1:N Relationships
		self.stations = []
		self.associations = []
		self.tree: Tree = AVL(id=1, on_rotation=self._handle_tree_rotation)
		# Auxiliary dictionary for O(1) access to events by ID
		self.events_dict: dict[int, Event] = {}
		self.versions: list[Version] = []
		self._suppress_undo_recording: bool = False

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
		# 4. REGISTRAR ACCIÓN DE DESHACER (SECCIÓN 13) E INSERTAR EN AVL
		# -----------------------------------------------------------------
		# Se toma una instantánea del estado antes de insertar el nuevo evento en el árbol
		# y en el catálogo. Si esta llamada proviene de process_report_step, _suppress_undo_recording
		# estará en True y no se duplicará la acción; si es creación manual, se apila normalmente.
		self._record_action("CREATE_EVENT", f"Create event ID {event_id}")

		new_node = Node(id=event_id, event=new_event)
		self.events_dict[event_id] = new_event
		# Si self.tree es una instancia de AVL, se inserta en él aplicando balanceo automático
		if hasattr(self, 'tree') and self.tree is not None:
			if hasattr(self.tree, 'insert'):
				self.tree.insert(new_node)

		if self.metrics is not None:
			self.metrics.active_events += 1
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

	# Method to process a single report from report_queue step by step --------------------------
	def process_report_step(self) -> dict | None:
		"""
		Procesa un único reporte de la cola report_queue (disparador paso a paso para UI/CLI).
		Retorna un diccionario con el resultado del paso, o None si la cola está vacía.
		
		Lógica de Deshacer (Sección 13):
		1. Registra la acción 'PROCESS_REPORT_STEP' ANTES de extraer el reporte (dequeue).
		   De este modo, al hacer undo_action, la cola recupera el reporte exactamente al frente.
		2. Se activa self._suppress_undo_recording = True en un bloque try/finally para que las
		   sub-operaciones (como crear evento en Regla 1 o editar en Regla 2) no generen
		   acciones secundarias indeseadas en la pila de deshacer.
		"""
		if self.report_queue is None or self.report_queue.is_empty():
			print("No reports in the queue to process.")
			return None

		# Registrar snapshot antes de extraer el reporte de la cola o mutar catálogos
		next_report = self.report_queue.current_reports[0] if (hasattr(self.report_queue, 'current_reports') and self.report_queue.current_reports) else None
		rep_desc = f"report ID {next_report.id} (rev {next_report.review})" if next_report else "report"
		self._record_action("PROCESS_REPORT_STEP", f"Process step for {rep_desc}")

		# Suprimir grabaciones anidadas durante la aplicación de reglas del reporte
		self._suppress_undo_recording = True
		try:
			# Rastrear rotaciones antes del paso para reportar rotaciones específicas de este reporte
			cases_before = self.metrics.cases if self.metrics is not None else {}
			turns_before = self.metrics.turns if self.metrics is not None else {}

			report = self.report_queue.dequeue()

			# Check if the report ID corresponds to a permanently deleted event
			if self.historic is not None and report.id in self.historic.deleted:
				print(f"Report ID {report.id} discarded: Event was previously deleted.")
				if self.metrics is not None:
					self.metrics.discarded_reports += 1
				decision = "Discarded: Event was previously deleted"
			else:
				event, is_archived = self._find_event(report.id)
				decision = self._apply_report_rules(report, event, is_archived)

			# Calculate rotations produced during this single step
			rotations_produced: dict[str, dict[str, int]] = {}
			if self.metrics is not None:
				cases_after = self.metrics.cases
				turns_after = self.metrics.turns
				cases_diff = {k: cases_after[k] - cases_before.get(k, 0) for k in cases_after if cases_after[k] > cases_before.get(k, 0)}
				turns_diff = {k: turns_after[k] - turns_before.get(k, 0) for k in turns_after if turns_after[k] > turns_before.get(k, 0)}
				if cases_diff or turns_diff:
					rotations_produced = {'cases': cases_diff, 'turns': turns_diff}

			step_result = {
				'report': report,
				'event_id': report.id,
				'station': report.origin_station,
				'review': report.review,
				'decision': decision,
				'rotations': rotations_produced
			}

			print(f"[Step Processed] Event: {report.id}, Revision: {report.review}, Station: {report.origin_station}, Decision: {decision}")
			return step_result
		finally:
			self._suppress_undo_recording = False

	# Method to process all report_queue reports in batch ---------------------------------------
	def process_report(self) -> list[dict]:
		"""
		Processes all reports currently in the queue until empty.
		Delegates each step to process_report_step to ensure identical behavior
		and returns a list with all step outcomes.
		"""
		if self.report_queue is None or self.report_queue.is_empty():
			print("No reports in the queue to process.")
			return []

		results: list[dict] = []
		while not self.report_queue.is_empty():
			step_res = self.process_report_step()
			if step_res is not None:
				results.append(step_res)

		print(f"Batch processing completed: {len(results)} reports processed.")
		return results

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
	def _apply_report_rules(self, report: Report, event: Event | None, is_archived: bool) -> str:
		"""
		Applies the 5 comparison rules between an incoming report and an existing event.
		Returns a string describing the decision taken.
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
				return "New Event Registered"
			return "Creation Failed"

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
			return "Correction Accepted"

		# Rule 3 & 4: Same revision
		if report.review == event.review:
			if self._has_same_physical_data(report, event):
				# Rule 3: Confirmation -> Add origin stations
				#add stations from report to the stations of the event
				if report.origin_station:
					for st in report.origin_station:
						event.add_origin_station(st)
				print(f"Report confirmed for Event {event.id}. Station(s) registered.")
				return "Confirmation"
			else:
				# Rule 4: Conflict -> Reject report, don't modify event
				if self.metrics is not None:
					self.metrics.conflicts += 1
				print(f"Conflict detected for Event {event.id} at review {report.review}. Report rejected.")
				return "Conflict (Rejected)"

		# Rule 5: Lower revision -> Discard old report
		if report.review < event.review:
			if self.metrics is not None:
				self.metrics.discarded_reports += 1
			print(f"Report discarded for Event {event.id}: Review {report.review} is older than current {event.review}.")
			return "Discarded: Outdated Revision"

		return "No Action"

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

		# Registrar snapshot en la pila de deshacer antes de modificar los datos físicos o la clave del árbol AVL
		self._record_action("EDIT_EVENT", f"Edit event ID {event_id}")

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

		# Registrar snapshot antes de eliminar el nodo del árbol AVL y removerlo de los catálogos
		self._record_action("REMOVE_EVENT", f"Remove event ID {event_id}")

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
		# Registrar la acción de archivo masivo como una única unidad atómica en la pila de deshacer
		self._record_action("ARCHIVE_SUBTREE", f"Archive subtree rooted at ID {best_root_node.id} ({len(nodes_to_archive)} events)")

		# Suprimir grabaciones anidadas: la Sección 13 estipula que las eliminaciones y rotaciones
		# internas de un archivo masivo no se deshacen por separado
		self._suppress_undo_recording = True
		try:
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
		finally:
			self._suppress_undo_recording = False

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

		# Guardar el estado previo en la pila de deshacer antes de adelantar el reloj de simulación
		previous_time = self.clock_simulation
		self._record_action("ADVANCE_CLOCK", f"Advance clock from {previous_time.isoformat()} to {target_time.isoformat()}")
		self.clock_simulation = target_time

		print(f"Clock advanced successfully: {previous_time.isoformat()} -> {self.clock_simulation.isoformat()}")
		return self.clock_simulation

	# =========================================================================
	#              SISTEMA DE PILA DE DESHACER (SECCIÓN 13 - SNAPSHOTS)
	# =========================================================================

	def _record_action(self, action_type: str, description: str) -> None:
		"""
		Registra una instantánea (snapshot / patrón Memento) en la pila de deshacer (undo_stack).
		
		Funcionamiento:
		1. Supresión de acciones anidadas: Si _suppress_undo_recording está activo (por ejemplo,
		   durante el procesamiento de un reporte que internamente crea o edita eventos, o en
		   un archivo masivo de subárbol), se ignora el registro interno para cumplir con la regla:
		   "Las inserciones y rotaciones internas de una corrección o archivo masivo no se deshacen por separado".
		2. Desacoplamiento de callback: El árbol AVL almacena un callback vinculado (_handle_tree_rotation)
		   hacia esta instancia de Observatory. Para evitar que copy.deepcopy intente clonar recursivamente
		   toda la instancia de Observatory a través de ese método ligado, se desacopla temporalmente
		   (asignando None) y se restaura inmediatamente en el bloque 'finally'.
		3. Preservación de identidad de objetos (Deepcopy unificado): Al clonar en una sola estructura
		   el árbol, el diccionario de eventos, el histórico, la cola, las métricas y las asociaciones,
		   Python garantiza que las referencias internas apunten a los mismos objetos en memoria
		   (es decir, node.event es exactamente la misma instancia que events_dict[node.id]).
		4. Almacenamiento en pila: Se crea un objeto Action con un ID autoincremental, tipo de acción,
		   descripción explicativa, la instantánea de estado y la marca de tiempo actual, apilándolo
		   en self.undo_stack.
		"""
		# Si hay una operación compuesta en curso, no registrar pasos internos secundarios
		if getattr(self, '_suppress_undo_recording', False):
			return

		# Asegurar que la pila de deshacer esté instanciada
		if self.undo_stack is None:
			self.undo_stack = Undo_stack()

		# Desvincular temporalmente el callback de rotación para evitar clonación circular del Observatorio
		original_callback = getattr(self.tree, '_AVL__on_rotation', None) if self.tree is not None else None
		if original_callback is not None:
			self.tree._AVL__on_rotation = None

		try:
			# Clonación profunda unificada para mantener coherencia e identidad referencial de los objetos
			copied_state = copy.deepcopy({
				'tree': self.tree,
				'events_dict': self.events_dict,
				'historic': self.historic,
				'report_queue': self.report_queue,
				'metrics': self.metrics,
				'associations': self.associations
			})
		finally:
			# Restaurar siempre el callback en el árbol activo en ejecución
			if original_callback is not None:
				self.tree._AVL__on_rotation = original_callback

		# Construir el diccionario de la instantánea con todos los componentes operativos
		snapshot = {
			'tree': copied_state['tree'],
			'events_dict': copied_state['events_dict'],
			'historic': copied_state['historic'],
			'report_queue': copied_state['report_queue'],
			'clock_simulation': self.clock_simulation,
			'limit': self.limit,
			'max_time': self.max_time,
			'distance_epicenter': self.distance_epicenter,
			'max_tree_age': self.max_tree_age,
			'stress_mode': self.stress_mode,
			'metrics': copied_state['metrics'],
			'associations': copied_state['associations']
		}
		
		# Crear la acción y apilarla en la estructura Undo_stack
		action_id = self.undo_stack.size() + 1
		action = Action(
			id=action_id,
			action_type=action_type,
			description=description,
			snapshot=snapshot,
			timestamp=datetime.now()
		)
		self.undo_stack.stack(action)

	def undo_action(self) -> bool:
		"""
		Deshace la última acción registrada en la pila (Sección 13).
		
		Funcionamiento:
		1. Extrae (desapila) la última Action de self.undo_stack.
		2. Restaura el estado completo del observatorio a partir del snapshot:
		   - Árbol AVL activo y sus enlaces de nodos.
		   - Diccionario de acceso rápido events_dict.
		   - Catálogo histórico (archivados y eliminados).
		   - Cola de reportes (restaura los reportes procesados a su posición en la cola).
		   - Reloj de simulación y parámetros de configuración.
		   - Métricas acumuladas y relaciones de asociación/réplicas.
		3. Reconecta el callback de rotaciones del árbol AVL restaurado hacia _handle_tree_rotation
		   para que cualquier operación futura continúe registrando rotaciones en Metrics.
		
		Retorna True si la acción se revirtió con éxito, o False si la pila estaba vacía.
		"""
		# Verificar si hay acciones previas disponibles para revertir
		if self.undo_stack is None or self.undo_stack.is_empty():
			print("No previous actions available to undo.")
			return False

		# Desapilar la acción más reciente
		last_action = self.undo_stack.unstack()
		s = last_action.snapshot

		# Restaurar el árbol AVL y reconectar el callback de rotación
		self.tree = s.get('tree')
		if self.tree is not None and hasattr(self.tree, '_AVL__on_rotation'):
			self.tree._AVL__on_rotation = self._handle_tree_rotation

		# Restaurar estructuras de datos y catálogos
		self.events_dict = s.get('events_dict', {})
		self.historic = s.get('historic')
		self.report_queue = s.get('report_queue')
		
		# Restaurar reloj de simulación y parámetros del observatorio
		self.clock_simulation = s.get('clock_simulation', self.clock_simulation)
		self.limit = s.get('limit', self.limit)
		self.max_time = s.get('max_time', self.max_time)
		self.distance_epicenter = s.get('distance_epicenter', self.distance_epicenter)
		self.max_tree_age = s.get('max_tree_age', self.max_tree_age)
		self.stress_mode = s.get('stress_mode', self.stress_mode)
		
		# Restaurar métricas acumuladas y asociaciones
		self.metrics = s.get('metrics')
		self.associations = s.get('associations', [])

		print(f"Undo completed successfully: Reverted '{last_action.description}' (Type: {last_action.action_type}).")
		return True
	
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
	
	def mark_as_reviewed(self, event_id: int) -> bool:
		# 1. Search for the event in the active catalog
		if not hasattr(self, 'events_dict') or event_id not in self.events_dict:
			print(f"Error: El evento con ID {event_id} no se encuentra en el catálogo activo.")
			return False

		event = self.events_dict[event_id]
		# 2. Validate that the event is not already marked as "Reviewed"
		if event.attention_state == "Reviewed":
			print(f"Aviso: El evento {event_id} ya se encuentra marcado como 'Reviewed'.")
			return True

		# Registrar instantánea en la pila de deshacer antes de mutar el estado de atención
		self._record_action("MARK_AS_REVIEWED", f"Mark event ID {event_id} as Reviewed")

		# 3. Change the attention state
		event.attention_state = "Reviewed"

		# 4. Update metrics if applicable
		if self.metrics is not None:
			pass # TODO: self.metrics.mark_reviewed_count += 1
		print(f"El evento {event_id} ha sido marcado exitosamente como 'Reviewed'.")
		return True

	# =========================================================================
	#              SISTEMA DE VERSIONES PERSISTENTES (SECCIÓN 13)
	# =========================================================================

	# Ruta absoluta del directorio donde se almacenarán las versiones físicas en formato JSON
	VERSIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saved_versions")

	def _serialize_scenario(self) -> dict:
		"""
		Serializa el escenario operativo completo a un diccionario compatible con JSON
		siguiendo las directrices de la Sección 12 (Guardado Estructural).
		
		Componentes serializados:
		1. Nodos y topología del árbol AVL activo (recorrido inorden conservando IDs de hijos y padre).
		2. Catálogo histórico: eventos archivados y eventos eliminados lógicamente con todos sus datos.
		3. Cola de reportes pendientes (FIFO).
		4. Catálogo de estaciones sismológicas registradas.
		5. Asociaciones sísmicas (eventos principales y sus réplicas asociadas).
		6. Contadores de métricas acumuladas (conflictos, correcciones, descartes y rotaciones LL, RR, LR, RL).
		7. Parámetros de configuración y reloj de simulación actual.
		"""
		# 1. Serializar nodos del árbol AVL activo y su topología física
		nodes_data = []
		if self.tree is not None and self.tree.root is not None:
			# El recorrido inorden garantiza una secuencia ordenada por clave de prioridad/magnitud/ID
			for node in self.tree.inorder():
				ev = node.event
				nodes_data.append({
					'id': node.id,
					'priority': ev.priority,
					'magnitude': ev.magnitude,
					'depth': ev.depth,
					'epicenter': list(ev.epicenter),
					'date_time': ev.date_time.isoformat(),
					'review': ev.review,
					'attention_state': ev.attention_state,
					'status': ev.status,
					'origin_stations': [st.id if hasattr(st, 'id') else str(st) for st in ev.origin_stations] if ev.origin_stations else [],
					'height': node.height,
					'balance_factor': node.balance_factor(),
					'left_son_id': node.left_son.id if node.left_son else None,
					'right_son_id': node.right_son.id if node.right_son else None,
					'father_id': node.father.id if node.father else None
				})

		# 2. Serializar Catálogo Histórico (archivados y eliminados lógicamente)
		archived_list = []
		deleted_list = []
		if self.historic is not None:
			# Eventos archivados por antigüedad y prioridad baja
			for ev in self.historic.archived.values():
				archived_list.append({
					'id': ev.id,
					'priority': ev.priority,
					'magnitude': ev.magnitude,
					'depth': ev.depth,
					'epicenter': list(ev.epicenter),
					'date_time': ev.date_time.isoformat(),
					'review': ev.review,
					'attention_state': ev.attention_state,
					'status': ev.status,
					'origin_stations': [st.id if hasattr(st, 'id') else str(st) for st in ev.origin_stations] if ev.origin_stations else []
				})
			# Eventos eliminados lógicamente (se guardan completos para poder reactivarlos si se requiere)
			for ev in self.historic.deleted.values():
				if ev is not None and hasattr(ev, 'priority'):
					deleted_list.append({
						'id': ev.id,
						'priority': ev.priority,
						'magnitude': ev.magnitude,
						'depth': ev.depth,
						'epicenter': list(ev.epicenter),
						'date_time': ev.date_time.isoformat(),
						'review': ev.review,
						'attention_state': ev.attention_state,
						'status': ev.status,
						'origin_stations': [st.id if hasattr(st, 'id') else str(st) for st in ev.origin_stations] if ev.origin_stations else []
					})
				elif ev is not None:
					deleted_list.append({'id': getattr(ev, 'id', ev)})

		# 3. Serializar la Cola de Reportes pendientes (FIFO)
		queue_list = []
		if self.report_queue is not None:
			for rep in self.report_queue.view_all():
				queue_list.append({
					'id': rep.id,
					'magnitude': rep.magnitude,
					'depth': rep.depth,
					'epicenter': list(rep.epicenter),
					'date_time': rep.date_time.isoformat(),
					'review': rep.review,
					'origin_station': [st.id if hasattr(st, 'id') else str(st) for st in rep.origin_station] if rep.origin_station else []
				})

		# 4. Serializar el Catálogo de Estaciones sismológicas
		stations_data = []
		if hasattr(self, 'stations') and self.stations:
			for st in self.stations:
				stations_data.append({
					'id': st.id,
					'name': st.name,
					'coords': list(st.coords)
				})

		# 5. Serializar las Asociaciones de réplicas sísmicas
		associations_data = []
		if hasattr(self, 'associations') and self.associations:
			for assoc in self.associations:
				associations_data.append({
					'id': assoc.id,
					'chosen_reference_id': assoc.chosen_reference.id if assoc.chosen_reference else None,
					'referenced_by_ids': [r.id for r in assoc.referenced_by if r]
				})

		# 6. Serializar Contadores de Métricas acumuladas y rotaciones
		metrics_data = {}
		if self.metrics is not None:
			metrics_data = {
				'conflicts': self.metrics.conflicts,
				'corrections_accepted': self.metrics.corrections_accepted,
				'discarded_reports': self.metrics.discarded_reports,
				'active_events': self.metrics.active_events,
				'removed_events': self.metrics.removed_events,
				'archived_events': self.metrics.archived_events,
				'cases': self.metrics.cases,
				'turns': self.metrics.turns
			}

		# Retornar estructura consolidada del escenario
		return {
			'clock_simulation': self.clock_simulation.isoformat(),
			'parameters': {
				'limit': self.limit,
				'max_time': self.max_time,
				'distance_epicenter': self.distance_epicenter,
				'max_tree_age': self.max_tree_age,
				'stress_mode': self.stress_mode
			},
			'metrics': metrics_data,
			'tree_root_id': self.tree.root.id if (self.tree and self.tree.root) else None,
			'active_nodes': nodes_data,
			'historic': {
				'archived': archived_list,
				'deleted': deleted_list
			},
			'report_queue': queue_list,
			'stations': stations_data,
			'associations': associations_data
		}

	def _deserialize_scenario(self, data: dict) -> None:
		"""
		Restaura el estado operativo del observatorio a partir de un diccionario serializado.
		
		Pasos de reconstrucción:
		1. Restablece el reloj de simulación y los parámetros globales de umbrales.
		2. Asegura que los componentes operativos esenciales no sean None.
		3. Restaura las métricas de negocio y los contadores acumulados de rotaciones AVL.
		4. Reconstruye el catálogo de estaciones para asegurar resolución de objetos Station reales.
		5. Restaura el catálogo histórico (archivados y eliminados lógicamente).
		6. Vacía y recarga la cola de reportes con instancias Report válidas.
		7. Reconstruye directamente la topología del árbol AVL (nodos, punteros hijo/padre)
		   sin ejecutar inserciones repetidas, conservando la forma exacta guardada.
		8. Recalcula las alturas de los nodos en post-orden (bottom-up) para garantizar
		   integridad matemática absoluta de alturas y factores de equilibrio en el árbol AVL.
		9. Reconecta el callback de rotaciones del árbol hacia _handle_tree_rotation.
		10. Restaura las asociaciones vinculando las réplicas a los eventos correspondientes.
		"""
		# 1. Restaurar reloj de simulación y parámetros operativos
		self.clock_simulation = datetime.fromisoformat(data['clock_simulation'])
		params = data.get('parameters', {})
		self.limit = params.get('limit', 3)
		self.max_time = params.get('max_time', 48.0)
		self.distance_epicenter = params.get('distance_epicenter', 40.0)
		self.max_tree_age = params.get('max_tree_age', 72)
		self.stress_mode = params.get('stress_mode', False)

		# 2. Asegurar que los componentes centrales existan (evitar errores si eran None)
		if self.metrics is None:
			self.metrics = Metrics()
		if self.historic is None:
			self.historic = Historic()
		if self.report_queue is None:
			self.report_queue = Report_Queue()
		if self.tree is None:
			self.tree = AVL(id=1, on_rotation=self._handle_tree_rotation)

		# Sincronizar el modo de estrés con el árbol AVL restaurado
		self.tree.stress_mode = self.stress_mode

		# 3. Restaurar métricas acumuladas y contadores de rotaciones (casos LL, RR, LR, RL y giros)
		if 'metrics' in data and self.metrics is not None:
			m = data['metrics']
			self.metrics.conflicts = m.get('conflicts', 0)
			self.metrics.corrections_accepted = m.get('corrections_accepted', 0)
			self.metrics.discarded_reports = m.get('discarded_reports', 0)
			self.metrics.active_events = m.get('active_events', 0)
			self.metrics.removed_events = m.get('removed_events', 0)
			self.metrics.archived_events = m.get('archived_events', 0)
			if 'cases' in m and isinstance(m['cases'], dict):
				self.metrics._cases.update(m['cases'])
			if 'turns' in m and isinstance(m['turns'], dict):
				self.metrics._turns.update(m['turns'])

		# 4. Reconstruir catálogo de estaciones sismológicas
		if not hasattr(self, 'stations') or self.stations is None:
			self.stations = []
		stations_by_id = {st.id: st for st in self.stations}
		for st_data in data.get('stations', []):
			if st_data['id'] not in stations_by_id:
				st_obj = Station(id=st_data['id'], name=st_data['name'], coords=tuple(st_data['coords']))
				self.stations.append(st_obj)
				stations_by_id[st_obj.id] = st_obj

		# Función auxiliar para resolver referencias a objetos reales de tipo Station
		# (necesario porque el setter de Report.origin_station valida estrictamente isinstance(item, Station))
		def _resolve_stations(station_refs: list) -> list:
			resolved = []
			for ref in station_refs:
				st_id = ref if isinstance(ref, int) else (ref.get('id') if isinstance(ref, dict) else None)
				if st_id is not None and st_id in stations_by_id:
					resolved.append(stations_by_id[st_id])
				elif st_id is not None:
					new_st = Station(id=st_id, name=f"Estacion_{st_id}", coords=(0.0, 0.0))
					self.stations.append(new_st)
					stations_by_id[st_id] = new_st
					resolved.append(new_st)
				elif isinstance(ref, Station):
					resolved.append(ref)
			return resolved

		# 5. Restaurar catálogo histórico
		self.historic.archived.clear()
		self.historic.deleted.clear()
		if 'historic' in data:
			# Eventos archivados
			for item in data['historic'].get('archived', []):
				ev = Event(
					id=item['id'],
					priority=item['priority'],
					magnitude=item['magnitude'],
					depth=item['depth'],
					epicenter=tuple(item['epicenter']),
					date_time=datetime.fromisoformat(item['date_time']),
					review=item['review'],
					attention_state=item['attention_state'],
					status=item['status']
				)
				ev.origin_stations = _resolve_stations(item.get('origin_stations', []))
				self.historic.archived[ev.id] = ev

			# Eventos eliminados lógicamente (se instancian como Event válidos para evitar errores de tipo)
			for item in data['historic'].get('deleted', []):
				if isinstance(item, dict) and 'priority' in item:
					ev = Event(
						id=item['id'],
						priority=item['priority'],
						magnitude=item['magnitude'],
						depth=item['depth'],
						epicenter=tuple(item['epicenter']),
						date_time=datetime.fromisoformat(item['date_time']),
						review=item['review'],
						attention_state=item['attention_state'],
						status=item['status']
					)
					ev.origin_stations = _resolve_stations(item.get('origin_stations', []))
					self.historic.deleted[ev.id] = ev
				elif isinstance(item, dict) and 'id' in item:
					del_id = item['id']
					self.historic.deleted[del_id] = Event(
						id=del_id, priority=1, magnitude=0.0, depth=0.0,
						epicenter=(0.0, 0.0), date_time=datetime.now(), review=1, status="Deleted"
					)
				elif isinstance(item, int):
					self.historic.deleted[item] = Event(
						id=item, priority=1, magnitude=0.0, depth=0.0,
						epicenter=(0.0, 0.0), date_time=datetime.now(), review=1, status="Deleted"
					)

		# 6. Restaurar cola de reportes pendientes
		while not self.report_queue.is_empty():
			self.report_queue.dequeue()

		for rep_data in data.get('report_queue', []):
			rep_stations = _resolve_stations(rep_data.get('origin_station', []))
			rep = Report(
				id=rep_data['id'],
				magnitude=rep_data['magnitude'],
				depth=rep_data['depth'],
				epicenter=tuple(rep_data['epicenter']),
				date_time=datetime.fromisoformat(rep_data['date_time']),
				review=rep_data['review'],
				origin_station=rep_stations
			)
			self.report_queue.enqueue(rep)

		# 7. Reconstruir topología del árbol AVL activo sin reinserciones
		self.events_dict.clear()
		nodes_by_id = {}
		raw_nodes = data.get('active_nodes', [])

		for raw in raw_nodes:
			ev = Event(
				id=raw['id'],
				priority=raw['priority'],
				magnitude=raw['magnitude'],
				depth=raw['depth'],
				epicenter=tuple(raw['epicenter']),
				date_time=datetime.fromisoformat(raw['date_time']),
				review=raw['review'],
				attention_state=raw['attention_state'],
				status=raw['status']
			)
			ev.origin_stations = _resolve_stations(raw.get('origin_stations', []))
			self.events_dict[ev.id] = ev
			node = Node(id=ev.id, event=ev)
			# Guardar tupla con referencias a los IDs de hijos y padre para enlazarlos a continuación
			nodes_by_id[ev.id] = (node, raw.get('left_son_id'), raw.get('right_son_id'), raw.get('father_id'))

		# Enlazar los punteros directos (left_son, right_son, father) entre los nodos
		for node_id, (node, left_id, right_id, father_id) in nodes_by_id.items():
			if left_id is not None and left_id in nodes_by_id:
				node.left_son = nodes_by_id[left_id][0]
			if right_id is not None and right_id in nodes_by_id:
				node.right_son = nodes_by_id[right_id][0]
			if father_id is not None and father_id in nodes_by_id:
				node.father = nodes_by_id[father_id][0]

		# Asignar el nodo raíz del árbol AVL
		root_id = data.get('tree_root_id')
		if root_id is not None and root_id in nodes_by_id:
			self.tree.root = nodes_by_id[root_id][0]
		else:
			self.tree.root = None

		# 8. Recalcular alturas de nodos en recorrido post-orden (bottom-up: hojas hacia la raíz)
		# Esto garantiza que las alturas de los hijos siempre se calculen antes que las del padre
		def _recalculate_heights(current: Node | None) -> None:
			if current is None:
				return
			_recalculate_heights(current.left_son)
			_recalculate_heights(current.right_son)
			current.update_height()

		_recalculate_heights(self.tree.root)

		# 9. Reconectar callback de rotaciones para que el observatorio continúe registrando eventos
		if hasattr(self.tree, '_AVL__on_rotation'):
			self.tree._AVL__on_rotation = self._handle_tree_rotation

		# 10. Restaurar relaciones de asociaciones (sismos principales y sus réplicas)
		self.associations = []
		for a_data in data.get('associations', []):
			ref_id = a_data.get('chosen_reference_id')
			ref_ev = self.events_dict.get(ref_id) or (self.historic.archived.get(ref_id) if self.historic else None)
			if ref_ev:
				assoc_obj = Association(assoc_id=a_data['id'], chosen_reference=ref_ev)
				for r_id in a_data.get('referenced_by_ids', []):
					r_ev = self.events_dict.get(r_id) or (self.historic.archived.get(r_id) if self.historic else None)
					if r_ev:
						assoc_obj.referenced_by.append(r_ev)
				self.associations.append(assoc_obj)

	def save_version(self, name: str) -> bool:
		"""
		Guarda una versión con nombre del escenario operativo actual en un archivo persistente JSON.
		
		Funcionamiento:
		1. Normaliza el nombre eliminando espacios y caracteres no válidos.
		2. Asegura la existencia del directorio físico 'saved_versions/'.
		3. Serializa todo el estado llamando a _serialize_scenario() e incrusta metadatos (nombre, timestamp).
		4. Escribe el archivo JSON formateado con indentación legible.
		5. Actualiza la lista en memoria self.versions evitando duplicados si el nombre ya existía.
		"""
		if not name or not name.strip():
			print("Error: Version name cannot be empty.")
			return False

		# Limpiar el nombre para crear un archivo válido
		clean_name = name.strip().replace(" ", "_")
		os.makedirs(self.VERSIONS_DIR, exist_ok=True)
		file_path = os.path.join(self.VERSIONS_DIR, f"{clean_name}.json")

		# Generar payload serializado e incorporar metadatos de versión
		payload = self._serialize_scenario()
		payload['version_meta'] = {
			'name': clean_name,
			'saved_at': datetime.now().isoformat()
		}

		try:
			with open(file_path, 'w', encoding='utf-8') as f:
				json.dump(payload, f, indent=4, ensure_ascii=False)

			# Mantener registro en la lista self.versions sin duplicar si ya existía
			existing = next((v for v in self.versions if v.name == clean_name), None)
			if existing is not None:
				existing.date_created = datetime.now()
				existing.file_path = file_path
			else:
				version_obj = Version(
					id=len(self.versions) + 1,
					name=clean_name,
					date_created=datetime.now(),
					file_path=file_path
				)
				self.versions.append(version_obj)

			print(f"Version '{clean_name}' saved successfully to {file_path}.")
			return True
		except Exception as e:
			print(f"Error saving version '{clean_name}': {e}")
			return False

	def list_versions(self) -> list[str]:
		"""
		Retorna una lista ordenada con los nombres de todas las versiones persistentes disponibles en disco.
		Sincroniza automáticamente la lista en memoria self.versions si se detectan archivos nuevos.
		"""
		if not os.path.exists(self.VERSIONS_DIR):
			return []

		version_names = []
		for file in os.listdir(self.VERSIONS_DIR):
			if file.endswith(".json"):
				v_name = file[:-5]  # Elimina la extensión '.json'
				version_names.append(v_name)
				# Sincronizar self.versions si el archivo no estaba cargado en memoria previamente
				if not any(v.name == v_name for v in self.versions):
					f_path = os.path.join(self.VERSIONS_DIR, file)
					try:
						mtime = datetime.fromtimestamp(os.path.getmtime(f_path))
					except OSError:
						mtime = datetime.now()
					self.versions.append(Version(
						id=len(self.versions) + 1,
						name=v_name,
						date_created=mtime,
						file_path=f_path
					))
		return sorted(version_names)

	def restore_version(self, name: str) -> bool:
		"""
		Restaura una versión persistente guardada desde el disco.
		
		Regla de la Sección 13:
		Esta operación de restauración se registra como una acción deshacible en la pila
		undo_stack ('RESTORE_VERSION') antes de sobreescribir el catálogo, permitiendo
		al usuario deshacer la restauración y regresar al estado inmediatamente anterior.
		"""
		clean_name = name.strip().replace(" ", "_")
		file_path = os.path.join(self.VERSIONS_DIR, f"{clean_name}.json")

		# Validar que el archivo exista físicamente en el disco
		if not os.path.exists(file_path):
			print(f"Error: Version '{clean_name}' does not exist.")
			return False

		try:
			with open(file_path, 'r', encoding='utf-8') as f:
				data = json.load(f)

			# Registrar el estado actual en undo_stack antes de restaurar (permite deshacer la restauración)
			if hasattr(self, '_record_action'):
				self._record_action("RESTORE_VERSION", f"Restore version '{clean_name}'")

			# Aplicar la reconstrucción completa del estado
			self._deserialize_scenario(data)
			print(f"Version '{clean_name}' successfully restored into the observatory.")
			return True
		except Exception as e:
			print(f"Error restoring version '{clean_name}': {e}")
			return False

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
		return None

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
		estado_auditoria = {"clave_previa": None}

		def auditar_nodo(nodo) -> int:
			"""
			Recursive function that traverses the tree in in-order.
			Returns the recalculated height of the node.
			"""
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
			altura_real = 1 + max(altura_izq, altura_der)
			if nodo.height != altura_real:
				reporte.append(f"Error de Metadatos (ID {nodo.id}): Altura guardada={nodo.height}, Altura real={altura_real}.")

			# 6. Calculate and verify balance factor
			factor_calculado = altura_izq - altura_der
			
			if not self.stress_mode:
				if factor_calculado not in (-1, 0, 1):
					reporte.append(f"Error de Balance (Modo Normal): ID {nodo.id} tiene un factor de {factor_calculado}.")
			else:
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

