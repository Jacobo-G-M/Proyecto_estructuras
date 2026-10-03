from datetime import datetime

class Version:
	# ------------------------
	#       CONSTRUCTOR
	# ------------------------
	def __init__(self, id: int, name: str = "", date_created: datetime | None = None, file_path: str = ""):
		self.__id: int = id
		self.__name: str = name
		self.__date_created: datetime = date_created if date_created is not None else datetime.now()
		self.__file_path: str = file_path

	# ------------------------
	#   GETTERS AND SETTERS
	# ------------------------
	@property
	def id(self) -> int:
		return self.__id

	@id.setter
	def id(self, value: int) -> None:
		self.__id = value

	@property
	def name(self) -> str:
		return self.__name

	@name.setter
	def name(self, value: str) -> None:
		self.__name = value

	@property
	def date_created(self) -> datetime:
		return self.__date_created

	@date_created.setter
	def date_created(self, value: datetime) -> None:
		self.__date_created = value

	@property
	def file_path(self) -> str:
		return self.__file_path

	@file_path.setter
	def file_path(self, value: str) -> None:
		self.__file_path = value

	def __repr__(self) -> str:
		return f"Version(id={self.id}, name='{self.name}', created='{self.date_created.isoformat()}')"

