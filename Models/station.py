try:
    import Models.report as report_module
except ImportError:
    import report as report_module

class Station:
    def __init__(
        self,
        id: int,
        name: str,
        coords: tuple[float, float],
        my_reports: list = None,
    ):
        self.id = id
        self.name = name
        self.coords = coords
        self.my_reports = my_reports if my_reports is not None else []

    # --- id ---
    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        if not isinstance(value, int) or isinstance(value, bool):
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

    # --- coords ---
    @property
    def coords(self) -> tuple[float, float]:
        return self._coords

    @coords.setter
    def coords(self, value: tuple[float, float]):
        self._coords = self._validate_coord(value, "coords")

    # --- my_reports ---
    @property
    def my_reports(self) -> list:
        return self._my_reports

    @my_reports.setter
    def my_reports(self, value: list):
        if not isinstance(value, list):
            raise TypeError("my_reports must be a list.")
        if not all(isinstance(item, report_module.Report) for item in value):
            raise TypeError("all items in my_reports must be instances of Report.")
        self._my_reports = value
    
    # Internal helper method to validate coordinate tuples
    def _validate_coord(self, coord: tuple[float, float], field_name: str) -> tuple[float, float]:
        if not isinstance(coord, tuple) or len(coord) != 2:
            raise ValueError(f"{field_name} must be a tuple of exactly 2 elements (float, float).")
        return (float(coord[0]), float(coord[1]))

    def __repr__(self) -> str:
        report_ids = [r.id for r in self._my_reports if hasattr(r, "id")]
        return (
            f"Station(id={self._id}, name='{self._name}', "
            f"coords={self._coords}, my_reports_ids={report_ids})"
        )

    #--- methods ---

    #method to add a report
    def add_report(self, report):
        if not isinstance(report, report_module.Report):
            raise TypeError("report must be an instance of Report.")
        if report not in self._my_reports:
            self._my_reports.append(report)