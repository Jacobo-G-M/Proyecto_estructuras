import Models.zone as zone_module


class Geographical_map:
    def __init__(self, zones: list = None):
        self.zones = zones if zones is not None else []

    # --- zones (1 to many relationship with Zone) ---
    @property
    def zones(self) -> list:
        return self._zones

    @zones.setter
    def zones(self, value: list):
        if not isinstance(value, list):
            raise TypeError("zones must be a list.")
        if not all(isinstance(item, zone_module.Zone) for item in value):
            raise TypeError("all items in zones must be instances of Zone.")
        self._zones = value

    def __repr__(self) -> str:
        zone_ids = [z.id for z in self._zones if hasattr(z, "id")]
        return f"Geographical_map(zones_ids={zone_ids})"

    #--- methods ---

    #method to add a zone
    def add_zone(self, zone):
        if not isinstance(zone, zone_module.Zone):
            raise TypeError("zone must be an instance of Zone.")
        
        if any(z.id == zone.id for z in self._zones):
            raise ValueError(f"Zone with ID {zone.id} already exists in the map.")

        self._zones.append(zone)

    #method to remove a zone
    def remove_zone(self, zone):
        if not isinstance(zone, zone_module.Zone):
            raise TypeError("zone must be an instance of Zone.")
        if zone in self._zones:
            self._zones.remove(zone)  

    #method to search a zone by id
    def get_zone_by_id(self, zone_id: int):
        if not isinstance(zone_id, int) or isinstance(zone_id, bool):
            raise TypeError("zone_id must be an integer.")
        for zone in self._zones:
            if zone.id == zone_id:
                return zone
        return None
    
    def is_in_populated_zone(self, x: float, y: float):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise TypeError("x and y must be numbers.")
        for zone in self._zones:
            if zone.is_populated and zone.contains(x, y):
                return True
        return False