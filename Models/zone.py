class Zone:
    def __init__(
        self,
        id: int,
        name: str,
        is_populated: bool,
        ubication_x: tuple[float, float],
        ubication_y: tuple[float, float]
        ):
        self.id = id
        self.name = name
        self.is_populated = is_populated
        self.ubication_x = ubication_x
        self.ubication_y = ubication_y

    # --- id ---
    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        if not isinstance(value, int):
            raise TypeError("id must be an integer.")
        self._id = value

    # --- name ---
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise TypeError("name must be a string.")
        self._name = value

    # --- is_populated ---
    @property
    def is_populated(self) -> bool:
        return self._is_populated

    @is_populated.setter
    def is_populated(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("is_populated must be a boolean.")
        self._is_populated = value

    # --- ubication_x ---
    @property
    def ubication_x(self) -> tuple[float, float]:
        return self._ubication_x

    @ubication_x.setter
    def ubication_x(self, value: tuple[float, float]):
        self._ubication_x = self._validate_coord(value, "ubication_x")

    # --- ubication_y ---
    @property
    def ubication_y(self) -> tuple[float, float]:
        return self._ubication_y

    @ubication_y.setter
    def ubication_y(self, value: tuple[float, float]):
        self._ubication_y = self._validate_coord(value, "ubication_y")

    # Internal helper method to validate coordinate tuples
    def _validate_coord(self, coord: tuple[float, float], field_name: str) -> tuple[float, float]:
        if not isinstance(coord, tuple) or len(coord) != 2:
            raise ValueError(f"{field_name} must be a tuple of exactly 2 elements (float, float).")
        return (float(coord[0]), float(coord[1]))

    def __repr__(self) -> str:
        return (f"Zone(id={self._id}, name='{self._name}', "
                f"is_populated={self._is_populated}, "
                f"ubication_x={self._ubication_x}, ubication_y={self._ubication_y})")


    #--- method ---

    def contains(self, x: float, y: float) -> bool:
        x_min, x_max = self.ubication_x
        y_min, y_max = self.ubication_y
        return (x_min <= x <= x_max) and (y_min <= y <= y_max)