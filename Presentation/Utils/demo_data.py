"""
Presentation / Utils / demo_data.py
Loads realistic initial demo data (stations, zones, earthquakes) into the Observatory
to ensure all visualization views (Map, Tree, Dashboard) display live, interactive domain data.
"""

from datetime import datetime, timedelta
from Models.station import Station
from Models.zone import Zone
from Business.geographical_map import Geographical_map


def load_demo_data(observatory):
    """
    Populates the Observatory with realistic stations, geographical zones,
    and seismic events matching the 1000x1000 km reference layout.
    """
    if len(observatory.events_dict) > 0:
        return

    # 1. Configure Geographical Map & Zones
    if observatory.geographical_map is None or len(observatory.geographical_map.zones) == 0:
        z1 = Zone(
            id=1,
            name="Z-01 VALLE",
            ubication_x=(70.0, 390.0),
            ubication_y=(500.0, 840.0),
            is_populated=True
        )
        z2 = Zone(
            id=2,
            name="Z-02 COSTA",
            ubication_x=(550.0, 850.0),
            ubication_y=(160.0, 460.0),
            is_populated=True
        )
        z3 = Zone(
            id=3,
            name="Z-03 SIERRA",
            ubication_x=(520.0, 790.0),
            ubication_y=(650.0, 910.0),
            is_populated=False
        )
        z4 = Zone(
            id=4,
            name="Z-04 DESIERTO",
            ubication_x=(90.0, 350.0),
            ubication_y=(160.0, 400.0),
            is_populated=False
        )
        geo_map = Geographical_map(zones=[z1, z2, z3, z4])
        observatory.geographical_map = geo_map

    # 2. Configure 5 Monitoring Stations
    if not observatory.stations:
        st1 = Station(id=1, name="S-N1", coords=(221.5, 730.2))
        st2 = Station(id=2, name="S-N2", coords=(648.0, 371.9))
        st3 = Station(id=3, name="S-C1", coords=(672.3, 812.4))
        st4 = Station(id=4, name="S-S1", coords=(183.7, 281.0))
        st5 = Station(id=5, name="S-E1", coords=(819.2, 563.8))
        observatory.stations = [st1, st2, st3, st4, st5]

    st = observatory.stations[0]
    base_time = observatory.clock_simulation - timedelta(hours=2)

    # 3. Create Representative Earthquakes
    # Format: (id, mag, depth, epicenter, time_offset_h)
    demo_events = [
        # Eventos base representativos
        (42, 6.1, 18.0, (410.0, 390.0), 3.0),   # P3 (mag >= 6.0)
        (10, 5.2, 22.4, (412.0, 388.0), 2.5),   # P3 (mag >= 4.5, depth <= 30 en zona poblada)
        (31, 4.8, 45.0, (200.0, 150.0), 4.0),   # P2 (mag >= 4.5, depth > 30)
        (7,  3.1, 15.0, (150.0, 200.0), 5.0),   # P1 (mag < 4.5)
        (88, 4.4, 25.0, (420.0, 410.0), 1.0),   # P1 (mag < 4.5)
        (15, 3.9, 10.0, (220.0, 180.0), 6.0),   # P1
        (53, 2.7, 8.0,  (100.0, 120.0), 8.0),   # P1

        # Eventos adicionales para probar topología y Acceso Costoso (P3 depth > L=3)
        (65, 6.3, 15.0, (405.0, 395.0), 7.0),   # P3
        (72, 6.8, 12.0, (415.0, 400.0), 9.0),   # P3
        (81, 7.1, 20.0, (425.0, 405.0), 10.0),  # P3
        (94, 6.5, 25.0, (408.0, 392.0), 11.0),  # P3
        (24, 5.8, 19.0, (411.0, 389.0), 12.0),  # P3 (zona poblada)
        (19, 5.0, 21.0, (414.0, 387.0), 13.0),  # P3 (zona poblada)
        (5,  2.2, 5.0,  (80.0, 90.0),   14.0),  # P1 (profundidad 4 en árbol, NO costoso por ser P1)
        (61, 4.9, 50.0, (190.0, 160.0), 15.0),  # P2
        (38, 4.6, 60.0, (210.0, 140.0), 16.0),  # P2 (profundidad 4 en árbol, NO costoso por ser P2)
        (95, 6.6, 14.0, (407.0, 393.0), 18.0),  # P3 (profundidad 4 > L=3 -> ACCESO COSTOSO)
        (99, 7.5, 10.0, (430.0, 410.0), 17.0),  # P3 (profundidad 4 > L=3 -> ACCESO COSTOSO)
        (25, 5.9, 17.0, (409.0, 391.0), 19.0),  # P3 (zona poblada)
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

    # Archive a couple of events for historical testing
    try:
        if 1080 in observatory.events_dict:
            ev_arch = observatory.events_dict[1080]
            observatory.archive_event(ev_arch)
    except Exception:
        pass
