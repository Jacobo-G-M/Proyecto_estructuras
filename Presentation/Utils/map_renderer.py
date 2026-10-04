"""
Presentation / Utils / map_renderer.py
Rendering engine for the 1000x1000 km geographic seismological map.
Transforms geographical Cartesian domain coordinates to Tkinter Canvas pixels,
supports dynamic Pan & Zoom camera navigation, adaptive reticles,
geographic zones, monitoring stations, earthquakes, and replica vectors.
"""

import math
from typing import Optional, List, Tuple
import tkinter as tk

from Presentation.Components.theme import (
    BG_ROOT, ACCENT_CYAN, ACCENT_AMBER,
    BORDER_LINE, TEXT_PRIMARY, TEXT_MUTED,
    WARNING, DANGER, SUCCESS
)


class MapRenderer:
    """
    Stateless rendering helper that draws geographic layers onto a Tkinter Canvas.
    Supports responsive linear projection, camera Pan & Zoom view bounds,
    and layer visibility management.
    """

    # Canvas margins to leave space for axis labels and bounding lines
    MARGIN_LEFT = 36
    MARGIN_RIGHT = 16
    MARGIN_TOP = 16
    MARGIN_BOTTOM = 26

    # =============================================================
    # Coordinate Projection Utilities (Pan & Zoom aware)
    # =============================================================
    @classmethod
    def km_to_px(
        cls,
        km_x: float,
        km_y: float,
        canvas_w: int,
        canvas_h: int,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> Tuple[float, float]:
        """
        Projects Cartesian kilometers to Tkinter screen pixel coordinates.
        Uses view_bounds = (x_min, x_max, y_min, y_max) for Pan & Zoom.
        """
        usable_w = max(1, canvas_w - cls.MARGIN_LEFT - cls.MARGIN_RIGHT)
        usable_h = max(1, canvas_h - cls.MARGIN_TOP - cls.MARGIN_BOTTOM)

        x_min, x_max, y_min, y_max = view_bounds
        span_x = max(1.0, x_max - x_min)
        span_y = max(1.0, y_max - y_min)

        px = cls.MARGIN_LEFT + ((km_x - x_min) / span_x) * usable_w
        # Invert Y axis: y_min is at the bottom, y_max is at the top
        py = cls.MARGIN_TOP + (1.0 - ((km_y - y_min) / span_y)) * usable_h
        return px, py

    @classmethod
    def px_to_km(
        cls,
        px_x: float,
        px_y: float,
        canvas_w: int,
        canvas_h: int,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> Tuple[float, float]:
        """
        Converts Tkinter screen pixel coordinates back into Cartesian kilometers.
        Accounts for current Pan & Zoom view_bounds.
        """
        usable_w = max(1, canvas_w - cls.MARGIN_LEFT - cls.MARGIN_RIGHT)
        usable_h = max(1, canvas_h - cls.MARGIN_TOP - cls.MARGIN_BOTTOM)

        x_min, x_max, y_min, y_max = view_bounds
        span_x = max(1.0, x_max - x_min)
        span_y = max(1.0, y_max - y_min)

        km_x = x_min + ((px_x - cls.MARGIN_LEFT) / usable_w) * span_x
        km_y = y_min + (1.0 - ((px_y - cls.MARGIN_TOP) / usable_h)) * span_y

        clamped_x = max(0.0, min(1000.0, km_x))
        clamped_y = max(0.0, min(1000.0, km_y))
        return clamped_x, clamped_y

    @staticmethod
    def distance_km(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculates 2D Euclidean distance in kilometers between two points."""
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    # =============================================================
    # Master Render Pipeline
    # =============================================================
    @classmethod
    def render(
        cls,
        canvas: tk.Canvas,
        canvas_w: int,
        canvas_h: int,
        zones: Optional[list] = None,
        stations: Optional[list] = None,
        active_events: Optional[list] = None,
        archived_events: Optional[list] = None,
        grid_density: str = "100 km",
        show_zones: bool = True,
        show_stations: bool = True,
        show_active: bool = True,
        show_archived: bool = True,
        show_replicas: bool = True,
        selected_event = None,
        selected_station_id: Optional[int] = None,
        radius_km: int = 60,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> None:
        """
        Clears and completely redraws the map canvas in structured Z-order:
        1. Background & Reticle Grid
        2. Geographic Zones (Populated & Non-populated)
        3. Inspection Radius (R) & Replica Vectors
        4. Archived Events
        5. Active Events
        6. Monitoring Stations
        7. Margin Masking & Coordinate Axes
        """
        canvas.delete("all")

        if canvas_w < 80 or canvas_h < 80:
            return

        usable_w = max(1, canvas_w - cls.MARGIN_LEFT - cls.MARGIN_RIGHT)
        usable_h = max(1, canvas_h - cls.MARGIN_TOP - cls.MARGIN_BOTTOM)

        # 1. Base Grid & Background
        cls.draw_grid(canvas, canvas_w, canvas_h, density=grid_density, view_bounds=view_bounds)

        # 2. Zones Layer
        if show_zones and zones:
            cls.draw_zones(canvas, zones, canvas_w, canvas_h, view_bounds=view_bounds)

        # 3. Radius Circle and Replica Vectors
        if show_replicas and selected_event:
            cls.draw_replicas_and_radius(
                canvas=canvas,
                selected_event=selected_event,
                all_events=active_events or [],
                radius_km=radius_km,
                canvas_w=canvas_w,
                canvas_h=canvas_h,
                view_bounds=view_bounds
            )

        # 4. Archived Events Layer
        if show_archived and archived_events:
            cls.draw_archived_events(canvas, archived_events, canvas_w, canvas_h, view_bounds=view_bounds)

        # 5. Active Events Layer
        if show_active and active_events:
            cls.draw_active_events(
                canvas=canvas,
                events=active_events,
                selected_id=selected_event.id if selected_event else None,
                canvas_w=canvas_w,
                canvas_h=canvas_h,
                view_bounds=view_bounds
            )

        # 6. Monitoring Stations Layer
        if show_stations and stations:
            cls.draw_stations(
                canvas=canvas,
                stations=stations,
                canvas_w=canvas_w,
                canvas_h=canvas_h,
                selected_station_id=selected_station_id,
                view_bounds=view_bounds
            )

        # 7. Mask outside margins to keep clean boundaries
        cls.draw_margin_overlays(canvas, canvas_w, canvas_h, view_bounds=view_bounds, density=grid_density)

    # -------------------------------------------------------------
    # 1. Reticle Grid & Axes
    # -------------------------------------------------------------
    @classmethod
    def draw_grid(
        cls,
        canvas: tk.Canvas,
        canvas_w: int,
        canvas_h: int,
        density: str = "100 km",
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> None:
        """Draws the background canvas, boundary border, and adaptive grid lines."""
        usable_w = max(1, canvas_w - cls.MARGIN_LEFT - cls.MARGIN_RIGHT)
        usable_h = max(1, canvas_h - cls.MARGIN_TOP - cls.MARGIN_BOTTOM)

        # Canvas outer boundary box
        canvas.create_rectangle(
            cls.MARGIN_LEFT,
            cls.MARGIN_TOP,
            cls.MARGIN_LEFT + usable_w,
            cls.MARGIN_TOP + usable_h,
            outline=BORDER_LINE,
            width=1.5
        )

        density_lower = density.lower().strip()
        if "off" in density_lower:
            return

        x_min, x_max, y_min, y_max = view_bounds
        span_x = x_max - x_min

        # Adaptive step based on zoom span
        if span_x > 500:
            step = 100 if "100" in density_lower else 50
        elif span_x > 250:
            step = 50 if "100" in density_lower else 25
        elif span_x > 100:
            step = 20 if "100" in density_lower else 10
        else:
            step = 10 if "100" in density_lower else 5

        # Vertical grid lines
        first_x = math.ceil(x_min / step) * step
        km_curr = first_x
        while km_curr <= x_max:
            px, _ = cls.km_to_px(km_curr, 0, canvas_w, canvas_h, view_bounds=view_bounds)
            if cls.MARGIN_LEFT <= px <= cls.MARGIN_LEFT + usable_w:
                canvas.create_line(
                    px, cls.MARGIN_TOP,
                    px, cls.MARGIN_TOP + usable_h,
                    fill=BORDER_LINE,
                    width=1
                )
            km_curr += step

        # Horizontal grid lines
        first_y = math.ceil(y_min / step) * step
        km_curr = first_y
        while km_curr <= y_max:
            _, py = cls.km_to_px(0, km_curr, canvas_w, canvas_h, view_bounds=view_bounds)
            if cls.MARGIN_TOP <= py <= cls.MARGIN_TOP + usable_h:
                canvas.create_line(
                    cls.MARGIN_LEFT, py,
                    cls.MARGIN_LEFT + usable_w, py,
                    fill=BORDER_LINE,
                    width=1
                )
            km_curr += step

    @classmethod
    def draw_margin_overlays(
        cls,
        canvas: tk.Canvas,
        canvas_w: int,
        canvas_h: int,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0),
        density: str = "100 km"
    ) -> None:
        """
        Cleans up the margin areas outside the usable map box to prevent visual bleed,
        and renders the dynamic coordinate axis tick numbers.
        """
        usable_w = max(1, canvas_w - cls.MARGIN_LEFT - cls.MARGIN_RIGHT)
        usable_h = max(1, canvas_h - cls.MARGIN_TOP - cls.MARGIN_BOTTOM)

        # Masking rectangles covering margins
        canvas.create_rectangle(0, 0, cls.MARGIN_LEFT, canvas_h, fill="#0a141f", outline="")
        canvas.create_rectangle(0, 0, canvas_w, cls.MARGIN_TOP, fill="#0a141f", outline="")
        canvas.create_rectangle(cls.MARGIN_LEFT + usable_w, 0, canvas_w, canvas_h, fill="#0a141f", outline="")
        canvas.create_rectangle(0, cls.MARGIN_TOP + usable_h, canvas_w, canvas_h, fill="#0a141f", outline="")

        # Re-stroke boundary box
        canvas.create_rectangle(
            cls.MARGIN_LEFT,
            cls.MARGIN_TOP,
            cls.MARGIN_LEFT + usable_w,
            cls.MARGIN_TOP + usable_h,
            outline=BORDER_LINE,
            width=1.5
        )

        x_min, x_max, y_min, y_max = view_bounds
        span_x = x_max - x_min

        # Adaptive tick frequency for readable labels
        if span_x > 500:
            tick_step = 100
        elif span_x > 250:
            tick_step = 50
        elif span_x > 100:
            tick_step = 25
        else:
            tick_step = 10

        # Bottom axis numbers
        first_x = math.ceil(x_min / tick_step) * tick_step
        km_curr = first_x
        while km_curr <= x_max:
            px, _ = cls.km_to_px(km_curr, 0, canvas_w, canvas_h, view_bounds=view_bounds)
            if cls.MARGIN_LEFT <= px <= cls.MARGIN_LEFT + usable_w:
                canvas.create_text(
                    px, cls.MARGIN_TOP + usable_h + 10,
                    text=f"{int(km_curr)}",
                    fill=TEXT_MUTED,
                    font=("Consolas", 8)
                )
            km_curr += tick_step

        # Left axis numbers
        first_y = math.ceil(y_min / tick_step) * tick_step
        km_curr = first_y
        while km_curr <= y_max:
            _, py = cls.km_to_px(0, km_curr, canvas_w, canvas_h, view_bounds=view_bounds)
            if cls.MARGIN_TOP <= py <= cls.MARGIN_TOP + usable_h:
                canvas.create_text(
                    cls.MARGIN_LEFT - 14, py,
                    text=f"{int(km_curr)}",
                    fill=TEXT_MUTED,
                    font=("Consolas", 8)
                )
            km_curr += tick_step

    # -------------------------------------------------------------
    # 2. Geographic Zones
    # -------------------------------------------------------------
    @classmethod
    def draw_zones(
        cls,
        canvas: tk.Canvas,
        zones: list,
        canvas_w: int,
        canvas_h: int,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> None:
        """Draws bounded geographic zones (populated vs non-populated)."""
        x_min, x_max, y_min, y_max = view_bounds

        for zone in zones:
            try:
                zx_min, zx_max = zone.ubication_x
                zy_min, zy_max = zone.ubication_y
            except (AttributeError, TypeError, ValueError):
                continue

            # Cull zones outside current viewport
            if zx_max < x_min or zx_min > x_max or zy_max < y_min or zy_min > y_max:
                continue

            px1, py1 = cls.km_to_px(zx_min, zy_max, canvas_w, canvas_h, view_bounds=view_bounds)
            px2, py2 = cls.km_to_px(zx_max, zy_min, canvas_w, canvas_h, view_bounds=view_bounds)

            if zone.is_populated:
                outline_color = WARNING
                tag_text = f"{zone.name} · POB"
                dash_pattern = ()
                line_width = 1.5
            else:
                outline_color = TEXT_MUTED
                tag_text = f"{zone.name} · NO-POB"
                dash_pattern = (4, 4)
                line_width = 1.0

            canvas.create_rectangle(
                px1, py1, px2, py2,
                outline=outline_color,
                width=line_width,
                dash=dash_pattern
            )

            canvas.create_text(
                px1 + 6, py1 + 8,
                text=tag_text,
                anchor="nw",
                fill=outline_color,
                font=("Consolas", 8, "bold")
            )

    # -------------------------------------------------------------
    # 3. Monitoring Stations
    # -------------------------------------------------------------
    @classmethod
    def draw_stations(
        cls,
        canvas: tk.Canvas,
        stations: list,
        canvas_w: int,
        canvas_h: int,
        selected_station_id: Optional[int] = None,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> None:
        """Renders seismic monitoring stations as cyan triangles with code labels."""
        x_min, x_max, y_min, y_max = view_bounds

        for station in stations:
            try:
                sx, sy = station.coords
                sid = getattr(station, "id", None)
            except (AttributeError, TypeError, ValueError):
                continue

            if sx < x_min - 30 or sx > x_max + 30 or sy < y_min - 30 or sy > y_max + 30:
                continue

            px, py = cls.km_to_px(sx, sy, canvas_w, canvas_h, view_bounds=view_bounds)

            is_selected = (selected_station_id is not None and sid == selected_station_id)
            if is_selected:
                canvas.create_oval(
                    px - 14, py - 14,
                    px + 14, py + 14,
                    outline=ACCENT_CYAN,
                    width=1.5,
                    dash=(3, 3)
                )

            # Upward equilateral triangle
            points = [
                px, py - 9,
                px - 7, py + 5,
                px + 7, py + 5
            ]
            canvas.create_polygon(
                points,
                fill=ACCENT_CYAN,
                outline="#ffffff",
                width=1.5 if is_selected else 1
            )

            # Station name
            canvas.create_text(
                px, py + 14,
                text=station.name,
                fill="#ffffff" if is_selected else ACCENT_CYAN,
                font=("Consolas", 8, "bold")
            )

    # -------------------------------------------------------------
    # 4. Active Events
    # -------------------------------------------------------------
    @classmethod
    def draw_active_events(
        cls,
        canvas: tk.Canvas,
        events: list,
        selected_id: Optional[int],
        canvas_w: int,
        canvas_h: int,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> None:
        """Renders active earthquakes with priority color and magnitude-proportional radius."""
        x_min, x_max, y_min, y_max = view_bounds

        for event in events:
            try:
                ex, ey = event.epicenter
                mag = float(event.magnitude)
                priority = int(event.priority)
                eid = event.id
            except (AttributeError, TypeError, ValueError):
                continue

            if ex < x_min - 30 or ex > x_max + 30 or ey < y_min - 30 or ey > y_max + 30:
                continue

            px, py = cls.km_to_px(ex, ey, canvas_w, canvas_h, view_bounds=view_bounds)

            if priority >= 3:
                color = DANGER
            elif priority == 2:
                color = WARNING
            else:
                color = SUCCESS

            radius = max(4.5, mag * 2.6)

            is_selected = (selected_id is not None and str(eid) == str(selected_id))
            if is_selected or mag >= 6.0:
                canvas.create_oval(
                    px - (radius + 6), py - (radius + 6),
                    px + (radius + 6), py + (radius + 6),
                    outline=color,
                    width=1.2,
                    dash=(4, 4)
                )

            canvas.create_oval(
                px - radius, py - radius,
                px + radius, py + radius,
                fill=color,
                outline="#ffffff",
                width=1.5
            )

            label_text = f"EV-{eid} · M{mag:.1f}"
            canvas.create_text(
                px + radius + 5, py,
                text=label_text,
                anchor="w",
                fill="#ffffff" if is_selected else color,
                font=("Consolas", 8, "bold" if is_selected else "normal")
            )

    # -------------------------------------------------------------
    # 5. Archived Events
    # -------------------------------------------------------------
    @classmethod
    def draw_archived_events(
        cls,
        canvas: tk.Canvas,
        events: list,
        canvas_w: int,
        canvas_h: int,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> None:
        """Renders archived earthquakes as subtle hollow gray rings."""
        x_min, x_max, y_min, y_max = view_bounds

        for event in events:
            try:
                ex, ey = event.epicenter
            except (AttributeError, TypeError, ValueError):
                continue

            if ex < x_min - 20 or ex > x_max + 20 or ey < y_min - 20 or ey > y_max + 20:
                continue

            px, py = cls.km_to_px(ex, ey, canvas_w, canvas_h, view_bounds=view_bounds)
            r = 4.0

            canvas.create_oval(
                px - r, py - r,
                px + r, py + r,
                outline=TEXT_MUTED,
                width=1.2
            )

    # -------------------------------------------------------------
    # 6. Radius R & Replica Vectors
    # -------------------------------------------------------------
    @classmethod
    def draw_replicas_and_radius(
        cls,
        canvas: tk.Canvas,
        selected_event,
        all_events: list,
        radius_km: int,
        canvas_w: int,
        canvas_h: int,
        view_bounds: Tuple[float, float, float, float] = (0.0, 1000.0, 0.0, 1000.0)
    ) -> None:
        """
        Draws the circular inspection zone of radius R around the selected event,
        highlights candidate replicas in amber, and draws association vector lines.
        """
        try:
            cx, cy = selected_event.epicenter
        except (AttributeError, TypeError, ValueError):
            return

        c_px, c_py = cls.km_to_px(cx, cy, canvas_w, canvas_h, view_bounds=view_bounds)

        usable_w = max(1, canvas_w - cls.MARGIN_LEFT - cls.MARGIN_RIGHT)
        x_min, x_max, _, _ = view_bounds
        span_x = max(1.0, x_max - x_min)

        # Radius scaled dynamically by current zoom level
        radius_px = (radius_km / span_x) * usable_w

        # Inspection circle
        canvas.create_oval(
            c_px - radius_px, c_py - radius_px,
            c_px + radius_px, c_py + radius_px,
            outline=ACCENT_CYAN,
            width=1.5,
            dash=(6, 4)
        )

        # Inspection badge
        canvas.create_text(
            c_px - radius_px + 8, c_py - radius_px - 8,
            text=f"R = {radius_km} km · EV-{selected_event.id}",
            anchor="w",
            fill=ACCENT_CYAN,
            font=("Consolas", 8, "bold")
        )

        # Discover candidates inside radius R
        for other in all_events:
            if getattr(other, "id", None) == selected_event.id:
                continue

            try:
                ox, oy = other.epicenter
            except (AttributeError, TypeError, ValueError):
                continue

            dist = cls.distance_km((cx, cy), (ox, oy))
            if dist <= radius_km:
                o_px, o_py = cls.km_to_px(ox, oy, canvas_w, canvas_h, view_bounds=view_bounds)

                # Amber highlight halo around candidate
                canvas.create_oval(
                    o_px - 11, o_py - 11,
                    o_px + 11, o_py + 11,
                    outline=ACCENT_AMBER,
                    width=2
                )

                # Vector line connecting to the reference origin
                canvas.create_line(
                    o_px, o_py, c_px, c_py,
                    fill=ACCENT_AMBER,
                    width=1.5,
                    dash=(6, 4)
                )

                mid_x = (o_px + c_px) / 2
                mid_y = (o_py + c_py) / 2
                canvas.create_text(
                    mid_x, mid_y - 6,
                    text=f"R={dist:.0f}km",
                    fill=ACCENT_AMBER,
                    font=("Consolas", 7, "bold")
                )

    # =============================================================
    # Spatial Queries & Hit Testing
    # =============================================================
    @classmethod
    def find_nearest_event(
        cls,
        km_x: float,
        km_y: float,
        events: list,
        max_dist_km: float = 35.0
    ):
        """Finds the event closest to (km_x, km_y) within the given distance threshold."""
        closest = None
        min_dist = float("inf")

        for event in events:
            try:
                ex, ey = event.epicenter
            except (AttributeError, TypeError, ValueError):
                continue

            dist = cls.distance_km((km_x, km_y), (ex, ey))
            if dist <= max_dist_km and dist < min_dist:
                min_dist = dist
                closest = event

        return closest

    @classmethod
    def find_nearest_station(
        cls,
        km_x: float,
        km_y: float,
        stations: list
    ) -> Tuple[Optional[object], float]:
        """Finds the monitoring station closest to (km_x, km_y) and returns (station, distance_km)."""
        closest = None
        min_dist = float("inf")

        for station in stations:
            try:
                sx, sy = station.coords
            except (AttributeError, TypeError, ValueError):
                continue

            dist = cls.distance_km((km_x, km_y), (sx, sy))
            if dist < min_dist:
                min_dist = dist
                closest = station

        return closest, min_dist