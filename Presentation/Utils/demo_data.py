from datetime import datetime, timedelta
from Models.station import Station
from Models.zone import Zone
from Business.geographical_map import Geographical_map

def load_demo_data(observatory):
    """
    Carga un conjunto inicial de estaciones y eventos sismológicos realistas
    para que el sistema arranque con datos operativos interactivos.
    """
    if len(observatory.events_dict) > 0:
        return

    # 1. Configurar mapa y zonas pobladas
    if observatory.geographical_map is None:
        z1 = Zone(
            id=1,
            name="Zona Central Metropolitana",
            ubication_x=(300.0, 500.0),
            ubication_y=(300.0, 500.0),
            is_populated=True
        )
        geo_map = Geographical_map(zones=[z1])
        observatory.geographical_map = geo_map

    # 2. Configurar estaciones
    if not observatory.stations:
        st1 = Station(id=1, name="S-N1", coords=(250.0, 350.0))
        st2 = Station(id=2, name="S-N2", coords=(400.0, 420.0))
        st3 = Station(id=3, name="S-C1", coords=(600.0, 500.0))
        observatory.stations = [st1, st2, st3]

    st = observatory.stations[0]
    base_time = observatory.clock_simulation - timedelta(hours=2)

    # 3. Insertar eventos de prueba representativos
    # Formato: (id, mag, depth, epicenter, time_offset_h)
    demo_events = [
        (42, 6.1, 18.0, (410.0, 390.0), 3.0),   # P3 (mag >= 6.0)
        (10, 5.2, 22.4, (412.0, 388.0), 2.5),   # P3 (mag >= 4.5, depth <= 30 en zona poblada)
        (31, 4.8, 45.0, (200.0, 150.0), 4.0),   # P2 (mag >= 4.5, depth > 30)
        (7,  3.1, 15.0, (150.0, 200.0), 5.0),   # P1 (mag < 4.5)
        (88, 4.4, 25.0, (420.0, 410.0), 1.0),   # P1 (mag < 4.5)
        (15, 3.9, 10.0, (220.0, 180.0), 6.0),   # P1
        (53, 2.7, 8.0,  (100.0, 120.0), 8.0),   # P1
    ]

    for eid, mag, dep, epi, off in demo_events:
        dt = base_time - timedelta(hours=off)
        try:
            observatory.create_event(
                event_id=eid,
                magnitude=mag,
                depth=dep,
                epicenter=epi,
                date_time=dt,
                station=st
            )
        except Exception:
            pass
