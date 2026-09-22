class Historic:
    def __init__(self) -> None:
        #Attributes
        self._archived: list[Event] = []
        self._deleted: list[Event] = []

    # GETTER _archived
    @property
    def archived(self) -> list[Event]:
        return self._archived

    # SETTER _archived
    @archived.setter
    def archived(self, new_list: list[Event]) -> None:
        if isinstance(new_list, list):
            self._archived = new_list
        else:
            raise TypeError("El atributo 'archived' debe ser una lista.")

    # GETTER  _deleted
    @property
    def deleted(self) -> list[Event]:
        return self._deleted

    # SETTER _deleted
    @deleted.setter
    def deleted(self, new_list: list[Event]) -> None:
        if isinstance(new_list, list):
            self._deleted = new_list
        else:
            raise TypeError("El atributo 'deleted' debe ser una lista.")

    # --- Auxiliary and Business Methods ---

    def _is_valid_event(self, event: Event) -> bool:
        return type(event).__name__ == 'Event'

    def archive_event(self, event: Event) -> None:
        if self._is_valid_event(event):
            self._archived.append(event)
            print("Evento archivado con éxito.")
        else:
            raise TypeError("Error: El objeto ingresado no es de la clase Event.")

    def delete_event(self, event: Event) -> None:
        if self._is_valid_event(event):
            self._deleted.append(event)
            print("Evento eliminado con éxito.")
        else:
            raise TypeError("Error: El objeto ingresado no es de la clase Event.")