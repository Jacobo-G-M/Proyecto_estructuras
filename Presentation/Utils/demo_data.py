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
        (1042, 6.1, 22.4, (412.0, 388.0), 1.5),  # P3 (Priority 3, main shock)
        (1055, 5.2, 18.0, (600.0, 400.0), 2.0),  # P2 / P3
        (1039, 4.8, 15.0, (430.0, 410.0), 6.0),  # Candidate in R
        (1048, 4.1, 12.0, (470.0, 440.0), 4.5),  # Candidate in R
        (1012, 3.8, 25.0, (260.0, 500.0), 8.0),  # P1
        (1067, 3.2, 10.0, (740.0, 300.0), 3.2),  # P1
        (1080, 2.9,  8.0, (180.0, 220.0), 12.0), # P1
        (1095, 4.4, 30.0, (680.0, 750.0), 5.0),  # P2
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
