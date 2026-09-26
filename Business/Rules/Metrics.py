class Metrics:

		def __init__(self) -> None:
				self._corrections_accepted: int = 0
				self._discarded_reports: int = 0

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

		# Method to count active events pending review
		def pending_events(self, nodes: list) -> int:
			if not nodes:
				return 0
			return sum(1 for node in nodes if
									node.event and
									str(node.event.attention_state).strip().lower() in
									("pending", "pendiente"))

		# Method to count active events already reviewed
		def reviewed_events(self, nodes: list) -> int:
			if not nodes:
				return 0
			return sum(1 for node in nodes if
									node.event and
									str(node.event.attention_state).strip().lower() in
									("reviewed", "revisado"))

		def active_events(self) -> int:
				pass

		def archived_events(self) -> int:
				pass

		def events_by_priority(self) -> None:
				pass