class Version:
# ------------------------
#       CONSTRUCTOR
# ------------------------
  def __init__(self, id: int):
    self.__id: int = id 

# ------------------------
#   GETTERS AND SETTERS
# ------------------------
    @property
    def id(self) -> int:
        return self.__id

    @id.setter
    def id(self, value: int) -> None:
        self.__id = value
