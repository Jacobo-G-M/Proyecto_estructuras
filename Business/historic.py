from Business.Event import Event
class Historic:
    def __init__(self) -> None:
        #Attributes
        self._archived: dict[int, Event] = {}
        self._deleted: dict[int, Event] = {}

    # GETTER _archived
    @property
    def archived(self) -> dict[int, Event]:
        return self._archived

    # SETTER _archived
    @archived.setter
    def archived(self, new_dict: dict[int, Event]) -> None:
        if isinstance(new_dict, dict):
            self._archived = new_dict
        else:
            raise TypeError("El atributo 'archived' debe ser un diccionario.")

    # GETTER  _deleted
    @property
    def deleted(self) -> dict[int, Event]:
        return self._deleted

    # SETTER _deleted
    @deleted.setter
    def deleted(self, new_dict: dict[int, Event]) -> None:
        if isinstance(new_dict, dict):
            self._deleted = new_dict
        else:
            raise TypeError("El atributo 'deleted' debe ser un diccionario.")

    # --- Auxiliary and Business Methods ---

    def _is_valid_event(self, event: Event) -> bool:
        return type(event).__name__ == 'Event'

    def archive_event(self, event: Event) -> None:
        if self._is_valid_event(event):
            event.status = "Archived"
            self._archived[event.id] = event
            print("Evento archivado con éxito.")
        else:
            raise TypeError("Error: El objeto ingresado no es de la clase Event.")

    def delete_event(self, event: Event) -> None:
        if self._is_valid_event(event):
            event.status = "Deleted"
            self._deleted[event.id] = event
            print("Evento eliminado con éxito.")
        else:
            raise TypeError("Error: El objeto ingresado no es de la clase Event.")

    def unarchive_event(self, event_id: int) -> Event | None:
        #Ectraction: Extract the event from the archived dictionary by ID and restore its state.
        if event_id in self._archived:
            event = self._archived.pop(event_id)
            event.status = "Active"
            print(f"Evento {event.id} retirado del archivo y reactivado.")
            return event
        print("El evento no se encuentra en el archivo.")
        return None

    def undelete_event(self, event_id: int) -> Event | None:
        #Ectraction: Extract the event from the deleted dictionary by ID and restore its state.
        if event_id in self._deleted:
            event = self._deleted.pop(event_id)
            event.status = "Active"
            print(f"Evento {event.id} recuperado del historial de eliminados.")
            return event
            
        print("El evento no se encuentra en eliminados.")
        return None  