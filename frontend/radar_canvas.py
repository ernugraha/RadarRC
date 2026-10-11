# frontend/radar_canvas.py
# RadarRC - ATC24 Radar UI (final v11) - Rounded Panel Fixed + Optimized Performance

import tkinter as tk
import math
import time
import os
import sqlite3
from PIL import Image, ImageTk
from . import config
from .airlines import get_airline_name, get_airline_keys, get_airline_icao
from .airports import get_airport_name
from .aircraft_icons import SHAPES, classify_aircraft
from .map_renderer import MapRenderer


class RadarCanvas:
    def __init__(self, parent):
        self.parent = parent
        self.canvas = tk.Canvas(
            parent,
            width=config.WINDOW_WIDTH,
            height=config.WINDOW_HEIGHT,
            bg=config.BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.w = config.WINDOW_WIDTH
        self.h = config.WINDOW_HEIGHT
        self.cx = (config.SIDEBAR_WIDTH + self.w) // 2
        self.cy = (config.HEADER_HEIGHT + self.h - config.FOOTER_HEIGHT) // 2

        self.view_x = 0.0
        self.view_y = 0.0
        self.zoom = 1.0

        self._data = {}
        self._prev_data = {}
        self._prev_time = time.time()
        self._dyn_scale = config.SCALE
        self._dyn_center = (config.CENTER_X, config.CENTER_Y)
        self._fitted = False

        self.selected_callsign = None

        self._image_cache = {}
        self._current_photo = None

        self._drag_start = None
        self._drag_view_start = (0.0, 0.0)
        self._drag_moved = False

        # === OPTIMASI PERFORMA ===
        self._zoom_timer = None
        self._map_photo_cache = []

        # Map
        self.map_renderer = MapRenderer(maps_dir="assets/maps")
        self.map_renderer.load_all()
        self.show_map = True

        # Search box
        self._search_query = ""
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = tk.Entry(
            parent,
            textvariable=self.search_var,
            bg="#152238",
            fg=config.TEXT_COLOR,
            insertbackground=config.ACCENT_COLOR,
            relief="flat",
            font=("Consolas", 10),
            highlightthickness=1,
            highlightbackground=config.PANEL_BORDER,
            highlightcolor=config.ACCENT_COLOR,
            bd=0,
        )
        self.search_entry.bind("<Escape>", self._on_search_escape)
        self.search_entry.place(
            x=8,
            y=config.HEADER_HEIGHT + 36,
            width=config.SIDEBAR_WIDTH - 16,
            height=24,
        )
        self.search_entry.lift()

        self.sidebar_scroll = 0
        self.panel_scroll = 0
        self._hovered_callsign = None

        # Trail DB
        self._trail_db = None
        self._trail_cache = {}
        self._trail_cache_time = 0
        self._init_trail_db()

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel_linux)
        self.canvas.bind("<Button-5>", self._on_wheel_linux)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind_all("<KeyPress-r>", self._on_reset)
        self.canvas.bind_all("<KeyPress-R>", self._on_reset)
        self.canvas.bind_all("<KeyPress-f>", self._on_reset)
        self.canvas.bind_all("<KeyPress-F>", self._on_reset)
        self.canvas.bind_all("<KeyPress-c>", self._on_clear_trails)
        self.canvas.bind_all("<KeyPress-C>", self._on_clear_trails)
        self.canvas.bind_all("<KeyPress-m>", self._on_toggle_map)
        self.canvas.bind_all("<KeyPress-M>", self._on_toggle_map)
        self.canvas.bind_all("<Escape>", self._on_deselect)
        self.canvas.tag_bind("btn_chat_gen", "<Button-1>", self._open_chat_generator)
        self.canvas.tag_bind("btn_chat_gen", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("btn_chat_gen", "<Leave>", lambda e: self.canvas.config(cursor=""))

        self._redraw()

    # ================================================================
    # EVENTS
    # ================================================================

    def _open_chat_generator(self, event):
        from .chat_generator import ChatGeneratorWindow

        # Buka jendela baru jika belum ada
        if not hasattr(self, "chat_gen_window") or not self.chat_gen_window.winfo_exists():
            # Otomatis mengirim callsign pesawat yang sedang Anda klik!
            self.chat_gen_window = ChatGeneratorWindow(self.parent, callsign=self.selected_callsign or "")
        else:
            self.chat_gen_window.lift() # Bawa ke depan jika tertumpuk

    def _on_resize(self, event):
        self.w = event.width
        self.h = event.height
        self.cx = (config.SIDEBAR_WIDTH + self.w) // 2
        self.cy = (config.HEADER_HEIGHT + self.h - config.FOOTER_HEIGHT) // 2
        self._redraw()

    def _on_press(self, event):
        if event.y < config.HEADER_HEIGHT and 8 < event.x < 175:
            self._on_reset(None)
            return
        if event.x < config.SIDEBAR_WIDTH or event.y < config.HEADER_HEIGHT:
            return
        try:
            self.canvas.focus_set()
        except Exception:
            pass
        self._drag_start = (event.x, event.y)
        self._drag_view_start = (self.view_x, self.view_y)
        self._drag_moved = False

    def _on_drag(self, event):
        if self._drag_start is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]

        if abs(dx) > 3 or abs(dy) > 3:
            self._drag_moved = True

        self.canvas.move("map", dx, dy)
        self.canvas.move("plane", dx, dy)
        self.canvas.move("trail", dx, dy)
        self.canvas.move("origin", dx, dy)
        self.canvas.move("grid", dx, dy)

        self.view_x += dx
        self.view_y += dy

        # PERBAIKAN: Update titik awal drag agar pergerakan mulus
        self._drag_start = (event.x, event.y)

    def _on_release(self, event):
        if not self._drag_moved and self._drag_start is not None:
            self._try_select(event.x, event.y)
        else:
            # === OPTIMASI PAN: Redraw resolusi penuh saat dilepas ===
            self._redraw()
        self._drag_start = None

    def _try_select(self, mx, my):
        best = None
        best_dist = 15
        for cs, info in self._data.items():
            px, py = self._coord_to_screen(info.get("x", 0), info.get("y", 0))
            d = math.hypot(px - mx, py - my)
            if d < best_dist:
                best_dist = d
                best = cs
        self.selected_callsign = best
        self._redraw()

    def _on_motion(self, event):
        if event.x < config.SIDEBAR_WIDTH or event.y < config.HEADER_HEIGHT:
            if self._hovered_callsign is not None:
                self._hovered_callsign = None
                self._redraw()
            return
        if self.selected_callsign and event.x > self.w - 360:
            if self._hovered_callsign is not None:
                self._hovered_callsign = None
                self._redraw()
            return
        best = None
        best_dist = 18
        for cs, info in self._data.items():
            px, py = self._coord_to_screen(info.get("x", 0), info.get("y", 0))
            d = math.hypot(px - event.x, py - event.y)
            if d < best_dist:
                best_dist = d
                best = cs
        if best != self._hovered_callsign:
            self._hovered_callsign = best
            self._redraw()

    def _on_deselect(self, event):
        if self._is_search_focused():
            return
        self.selected_callsign = None
        self._redraw()

    def _on_wheel(self, event):
        if self.selected_callsign and event.x > self.w - 360:
            delta = -40 if event.delta > 0 else 40
            self.panel_scroll += delta
            self._draw_info_panel()  # HANYA render ulang panel kanan
            return
        if event.x < config.SIDEBAR_WIDTH and event.y > config.HEADER_HEIGHT:
            delta = -50 if event.delta > 0 else 50
            self.sidebar_scroll += delta
            self._draw_sidebar()  # HANYA render ulang panel kiri
            return
        factor = 1.15 if event.delta > 0 else 1 / 1.15
        self._apply_zoom(factor, event.x, event.y)

    def _on_wheel_linux(self, event):
        if self.selected_callsign and event.x > self.w - 360:
            delta = -40 if event.num == 4 else 40
            self.panel_scroll += delta
            self._draw_info_panel()  # HANYA render ulang panel kanan
            return
        if event.x < config.SIDEBAR_WIDTH and event.y > config.HEADER_HEIGHT:
            delta = -50 if event.num == 4 else 50
            self.sidebar_scroll += delta
            self._draw_sidebar()  # HANYA render ulang panel kiri
            return
        factor = 1.15 if event.num == 4 else 1 / 1.15
        self._apply_zoom(factor, event.x, event.y)

    def _on_reset(self, event):
        if self._is_search_focused():
            return
        self.sidebar_scroll = 0
        self._fitted = False
        if self._data:
            self._autofit()
            self._fitted = True
        self.view_x = 0.0
        self.view_y = 0.0
        self.zoom = 1.0
        self._redraw()

    def _on_clear_trails(self, event):
        if self._is_search_focused():
            return
        self._trail_cache.clear()
        self._redraw()

    def _on_toggle_map(self, event):
        if self._is_search_focused():
            return
        self.show_map = not self.show_map
        print(f"[RadarRC] Map: {'ON' if self.show_map else 'OFF'}")
        self._redraw()

    def _is_search_focused(self):
        try:
            return self.parent.focus_get() == self.search_entry
        except Exception:
            return False

    def _on_search_change(self, *args):
        self._search_query = self.search_var.get().strip().upper()
        self.sidebar_scroll = 0
        self._redraw()

    def _on_search_escape(self, event):
        self.search_var.set("")
        self.canvas.focus_set()
        return "break"

    def _get_filtered_data(self):
        if not self._search_query:
            return self._data
        return {
            cs: info for cs, info in self._data.items()
            if self._search_query in cs.upper()
        }

    def _is_matched(self, callsign):
        if not self._search_query:
            return False
        return self._search_query in callsign.upper()

    def _apply_zoom(self, factor, mx, my):
        nz = max(0.05, min(self.zoom * factor, 100.0))
        if nz == self.zoom:
            return
        s_old = self._dyn_scale * self.zoom
        s_new = self._dyn_scale * nz
        wx = (mx - self.cx - self.view_x) / s_old + self._dyn_center[0]
        wy = -(my - self.cy - self.view_y) / s_old + self._dyn_center[1]
        self.view_x = mx - self.cx - (wx - self._dyn_center[0]) * s_new
        self.view_y = my - self.cy + (wy - self._dyn_center[1]) * s_new
        self.zoom = nz

        # === OPTIMASI ZOOM (Debouncing) ===
        if self._zoom_timer is not None:
            self.parent.after_cancel(self._zoom_timer)

        self.canvas.delete("map")
        self.canvas.delete("trail")
        self.canvas.delete("origin")
        self.canvas.delete("grid")

        self._draw_planes()
        self._draw_sidebar()
        self._draw_info_panel()
        self._draw_header()
        self._draw_footer()

        self._zoom_timer = self.parent.after(150, self._redraw_after_zoom)

    def _redraw_after_zoom(self):
        self._zoom_timer = None
        self._redraw()

    # ================================================================
    # COORDINATE
    # ================================================================
    def _coord_to_screen(self, x, y):
        if config.FLIP_Y:
            y = -y
        s = self._dyn_scale * self.zoom
        px = self.cx + self.view_x + (x - self._dyn_center[0]) * s
        py = self.cy + self.view_y - (y - self._dyn_center[1]) * s
        return px, py

    def _autofit(self):
        if not self._data:
            return
        xs = [i.get("x", 0) for i in self._data.values()]
        ys = [i.get("y", 0) for i in self._data.values()]
        if config.FLIP_Y:
            ys = [-y for y in ys]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        if len(xs) <= 1:
            self._dyn_scale = config.SCALE
            self._dyn_center = (cx, cy)
            return
        max_dx = max(abs(x - cx) for x in xs)
        max_dy = max(abs(y - cy) for y in ys)
        span = max(max_dx, max_dy, 1)
        available = min(self.w - config.SIDEBAR_WIDTH, self.h) * 0.42
        self._dyn_scale = available / span
        self._dyn_center = (cx, cy)

    # ================================================================
    # TRAIL DB
    # ================================================================
    def _init_trail_db(self):
        from .paths import get_base_dir
        db_path = os.path.join(get_base_dir(), "data", "trails.db")
        if os.path.isfile(db_path):
            self._trail_db = db_path
            print(f"[RadarRC] Trail DB: {db_path}")
        else:
            print(f"[RadarRC] Trail DB belum ada: {db_path}")

    def _load_trail_from_db(self, callsign, max_age=3600):
        if not self._trail_db:
            return []
        try:
            cutoff = time.time() - max_age
            conn = sqlite3.connect(self._trail_db)
            c = conn.cursor()
            c.execute(
                "SELECT x, y FROM trails "
                "WHERE callsign = ? AND timestamp > ? "
                "ORDER BY timestamp ASC",
                (callsign, cutoff)
            )
            rows = c.fetchall()
            conn.close()
            return [(r[0], r[1]) for r in rows]
        except Exception as e:
            print(f"[RadarRC] DB error: {e}")
            return []

    def _refresh_trail_cache(self):
        now = time.time()
        if now - self._trail_cache_time < 1.0:
            return
        self._trail_cache_time = now
        if self.selected_callsign and self._trail_db:
            self._trail_cache[self.selected_callsign] = \
                self._load_trail_from_db(self.selected_callsign)

    def _update_trails(self):
        active = set(self._data.keys())
        for cs in list(self._trail_cache.keys()):
            if cs not in active:
                del self._trail_cache[cs]

    # ================================================================
    # HELPER: MODEL KEY & UTILS
    # ================================================================
    def _extract_model_key(self, aircraft_type):
        if not aircraft_type:
            return None
        t = aircraft_type.lower().replace(" ", "").replace("-", "")

        if "concorde" in t or t.startswith("conc"):
            return "concorde"
        if t.startswith("md") and any(c.isdigit() for c in t):
            nums = ''.join(c for c in t if c.isdigit())
            return f"md{nums}" if nums else "md11"

        for brand in ("airbus", "boeing", "cessna", "embraer", "bombardier"):
            if brand in t:
                nums = ''.join(c for c in t if c.isdigit())
                if nums:
                    return brand[0] + nums

        if "caravan" in t:
            return "caravan"
        return t

    def _find_aircraft_image(self, aircraft_type, callsign):
        if not os.path.isdir(config.ASSETS_DIR):
            return None
        model = self._extract_model_key(aircraft_type)
        airline_keys = get_airline_keys(callsign)
        candidates = []
        for akey in airline_keys:
            if model:
                candidates.append(f"{model}_{akey}.png")
                candidates.append(f"{akey}_{model}.png")
        if model:
            candidates.append(f"{model}.png")
        candidates.append("default.png")
        for name in candidates:
            path = os.path.join(config.ASSETS_DIR, name)
            if os.path.isfile(path):
                return path
        return None

    def _load_aircraft_image(self, path, max_w, max_h):
        key = (path, max_w, max_h)
        if key in self._image_cache:
            return self._image_cache[key]
        try:
            img = Image.open(path).convert("RGBA")
            iw, ih = img.size
            if iw == 0 or ih == 0:
                return None
            target_ratio = max_w / max_h
            img_ratio = iw / ih
            if img_ratio > target_ratio:
                new_h = max_h
                new_w = int(new_h * img_ratio)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                left = (new_w - max_w) // 2
                img = img.crop((left, 0, left + max_w, max_h))
            else:
                new_w = max_w
                new_h = int(new_w / img_ratio)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                top = (new_h - max_h) // 2
                img = img.crop((0, top, max_w, top + max_h))
            photo = ImageTk.PhotoImage(img)
            self._image_cache[key] = photo
            return photo
        except Exception as e:
            print(f"[RadarRC] Failed to load {path}: {e}")
            return None

    def _copy_to_clipboard(self, text):
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(text)
            print(f"[RadarRC] Copied: {text}")
        except Exception as e:
            print(f"[RadarRC] Copy failed: {e}")

    def _create_rounded_rect(self, x1, y1, x2, y2, radius=15, **kwargs):
        points = [
            x1+radius, y1, x1+radius, y1,
            x2-radius, y1, x2-radius, y1,
            x2, y1,
            x2, y1+radius, x2, y1+radius,
            x2, y2-radius, x2, y2-radius,
            x2, y2,
            x2-radius, y2, x2-radius, y2,
            x1+radius, y2, x1+radius, y2,
            x1, y2,
            x1, y2-radius, x1, y2-radius,
            x1, y1+radius, x1, y1+radius,
            x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    # ================================================================
    # DRAWING
    # ================================================================
    def _get_color(self, altitude, on_ground=False):
        if on_ground:
            return config.COLOR_GROUND
        if altitude < 2000:
            return config.COLOR_LOW
        elif altitude < 5000:
            return config.COLOR_MID
        return config.COLOR_HIGH

    def _draw_map(self):
        self.canvas.delete("map")
        self._map_photo_cache.clear()

        if not self.show_map:
            return

        # === OPTIMASI MAP: SVG Images Render ===
        if hasattr(self.map_renderer, 'images'):
            for layer_name, images_list in self.map_renderer.images.items():
                for img_info in images_list:
                    mx, my = img_info["x"], img_info["y"]
                    sx, sy = self._coord_to_screen(mx, my)

                    scale_factor = self._dyn_scale * self.zoom
                    disp_w = max(1, int(img_info["w"] * scale_factor))
                    disp_h = max(1, int(img_info["h"] * scale_factor))

                    try:
                        resized_img = img_info["image"].resize((disp_w, disp_h), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(resized_img)
                        self._map_photo_cache.append(photo)
                        self.canvas.create_image(sx, sy, image=photo, anchor="nw", tags="map")
                    except Exception as e:
                        print(f"[Map] Error resize: {e}")

        # Vektor
        layers = self.map_renderer.layers
        if "coast" in layers:
            for pts in layers["coast"]:
                screen = []
                for (mx, my) in pts:
                    sx, sy = self._coord_to_screen(mx, my)
                    screen.extend([sx, sy])
                if len(screen) >= 4:
                    self.canvas.create_line(
                        screen, fill=config.COAST_COLOR, width=1, tags="map"
                    )
        if "boundaries" in layers:
            for pts in layers["boundaries"]:
                screen = []
                for (mx, my) in pts:
                    sx, sy = self._coord_to_screen(mx, my)
                    screen.extend([sx, sy])
                if len(screen) >= 4:
                    self.canvas.create_line(
                        screen, fill=config.BOUNDARY_COLOR, width=1, tags="map"
                    )

    def _draw_grid(self):
        self.canvas.delete("grid")
        margin = 18
        self.canvas.create_text(
            (config.SIDEBAR_WIDTH + self.w) // 2,
            config.HEADER_HEIGHT + margin,
            text="N", fill=config.GRID_LABEL,
            font=("Helvetica", 10, "bold"), tags="grid"
        )
        self.canvas.create_text(
            self.w - margin,
            (config.HEADER_HEIGHT + self.h - config.FOOTER_HEIGHT) // 2,
            text="E", fill=config.GRID_LABEL,
            font=("Helvetica", 10, "bold"), tags="grid"
        )
        self.canvas.create_text(
            (config.SIDEBAR_WIDTH + self.w) // 2,
            self.h - config.FOOTER_HEIGHT - margin,
            text="S", fill=config.GRID_LABEL,
            font=("Helvetica", 10, "bold"), tags="grid"
        )
        self.canvas.create_text(
            config.SIDEBAR_WIDTH + margin,
            (config.HEADER_HEIGHT + self.h - config.FOOTER_HEIGHT) // 2,
            text="W", fill=config.GRID_LABEL,
            font=("Helvetica", 10, "bold"), tags="grid"
        )

    def _get_icon_size(self, selected=False):
        size = config.ICON_BASE_SIZE * max(
            config.ICON_MIN_MULT,
            min(config.ICON_MAX_MULT, self.zoom)
        )
        if selected:
            size *= config.ICON_SELECTED_BOOST
        return size

    def _draw_plane_icon(self, px, py, heading, color, aircraft_type,
                         selected=False, emergency=False):
        rad = math.radians(heading)
        size = self._get_icon_size(selected)

        if emergency:
            self.canvas.create_oval(
                px - size * 1.8, py - size * 1.8,
                px + size * 1.8, py + size * 1.8,
                outline="#ff0000", width=2, dash=(3, 2), tags="plane"
            )
        if selected:
            self.canvas.create_oval(
                px - size * 1.6, py - size * 1.6,
                px + size * 1.6, py + size * 1.6,
                outline=config.ACCENT_COLOR, width=2, dash=(4, 3), tags="plane"
            )

        kind = classify_aircraft(aircraft_type)
        if kind == "helicopter":
            self._draw_helicopter(px, py, heading, color, size)
            return
        if kind == "balloon":
            self._draw_balloon(px, py, color, size)
            return

        shape = SHAPES.get(kind) or SHAPES["narrow_body"]
        cos_h = math.cos(rad)
        sin_h = math.sin(rad)

        pts = []
        for lx, ly in shape:
            sx = lx * size
            sy = ly * size
            rx = sx * cos_h - sy * sin_h
            ry = sx * sin_h + sy * cos_h
            pts.extend([px + rx, py + ry])

        outline = config.ACCENT_COLOR if selected else "#0a0a0a"
        self.canvas.create_polygon(
            pts, fill=color, outline=outline, width=1, tags="plane"
        )

    def _draw_helicopter(self, px, py, heading, color, size):
        rad = math.radians(heading)
        cos_h = math.cos(rad)
        sin_h = math.sin(rad)

        def rot(lx, ly):
            return (px + lx * cos_h - ly * sin_h,
                    py + lx * sin_h + ly * cos_h)

        rotor_len = size * 1.4
        x0, y0 = rot(0, 0)
        for (bx, by) in [(rotor_len, rotor_len), (-rotor_len, rotor_len),
                         (-rotor_len, -rotor_len), (rotor_len, -rotor_len)]:
            x2, y2 = rot(bx, by)
            self.canvas.create_line(x0, y0, x2, y2,
                                    fill=color, width=2, tags="plane")
        tx1, ty1 = rot(0, 0)
        tx2, ty2 = rot(0, size * 1.3)
        self.canvas.create_line(tx1, ty1, tx2, ty2,
                                fill=color, width=3, tags="plane")
        self.canvas.create_oval(
            tx2 - 2, ty2 - 2, tx2 + 2, ty2 + 2,
            fill=color, outline="#0a0a0a", tags="plane"
        )
        bw = size * 0.4
        bh = size * 0.9
        self.canvas.create_oval(
            px - bw, py - bh, px + bw, py + bh,
            fill=color, outline="#0a0a0a", width=1, tags="plane"
        )

    def _draw_balloon(self, px, py, color, size):
        r = size * 0.9
        self.canvas.create_oval(
            px - r, py - r, px + r, py + r,
            fill=color, outline="#0a0a0a", width=1, tags="plane"
        )
        self.canvas.create_rectangle(
            px - r * 0.3, py + r * 1.0, px + r * 0.3, py + r * 1.3,
            fill="#8b7355", outline="#0a0a0a", tags="plane"
        )

    def _draw_trails(self):
        self.canvas.delete("trail")
        self.canvas.delete("origin")

        if not self.selected_callsign:
            return

        self._refresh_trail_cache()
        cs = self.selected_callsign
        trail = self._trail_cache.get(cs, [])
        if len(trail) < 2:
            return

        info = self._data.get(cs, {})
        color = self._get_color(
            info.get("altitude", 0),
            info.get("isOnGround", False)
        )

        screen = []
        for tx, ty in trail:
            px, py = self._coord_to_screen(tx, ty)
            screen.extend([px, py])
        self.canvas.create_line(screen, fill=color, width=2, tags="trail")

        for tx, ty in trail:
            px, py = self._coord_to_screen(tx, ty)
            self.canvas.create_oval(
                px - 1.5, py - 1.5, px + 1.5, py + 1.5,
                fill=color, outline="", tags="trail"
            )

        ox, oy = trail[0]
        opx, opy = self._coord_to_screen(ox, oy)
        self.canvas.create_oval(
            opx - 4, opy - 4, opx + 4, opy + 4,
            outline=config.ACCENT_COLOR, width=2, tags="origin"
        )
        self.canvas.create_text(
            opx, opy - 12, text="O",
            fill=config.ACCENT_COLOR,
            font=("Consolas", 9, "bold"), tags="origin"
        )

    def _draw_planes(self):
        self.canvas.delete("plane")
        for cs, info in self._data.items():
            try:
                x, y = info.get("x", 0), info.get("y", 0)
                heading = info.get("heading", 0)
                alt = info.get("altitude", 0)
                on_ground = info.get("isOnGround", False)
                emergency = info.get("isEmergency", False)
                ac_type = info.get("aircraftType", "")

                px, py = self._coord_to_screen(x, y)
                color = self._get_color(alt, on_ground)
                selected = (cs == self.selected_callsign)
                hovered = (cs == self._hovered_callsign)
                is_match = self._is_matched(cs)

                self._draw_plane_icon(
                    px, py, heading, color, ac_type, selected, emergency
                )

                if is_match and not selected and not hovered:
                    icon_size = self._get_icon_size()
                    self.canvas.create_oval(
                        px - icon_size * 1.6, py - icon_size * 1.6,
                        px + icon_size * 1.6, py + icon_size * 1.6,
                        outline="#2ecc71", width=1, dash=(2, 2), tags="plane"
                    )

                if selected or hovered:
                    fl = int(alt / 100) if alt else 0
                    text = f"{cs}  FL{fl:03d}"
                    tw = len(text) * 7 + 16
                    self.canvas.create_rectangle(
                        px - tw // 2, py - 32, px + tw // 2, py - 16,
                        fill="#ffffff", outline="#c8d1dc", width=1,
                        tags="plane"
                    )
                    self.canvas.create_text(
                        px, py - 24, text=text,
                        fill="#1a2733", anchor="center",
                        font=("Helvetica", 9, "bold"), tags="plane"
                    )
                    self.canvas.create_line(
                        px, py - 16, px, py - 10,
                        fill="#607080", width=1, tags="plane"
                    )
            except Exception as e:
                print(f"[RadarRC] Render error {cs}: {e}")

    def _draw_header(self):
        self.canvas.delete("header")
        self.canvas.create_rectangle(
            0, 0, self.w, config.HEADER_HEIGHT,
            fill=config.CARD_BG, outline="", tags="header"
        )
        self.canvas.create_line(
            0, config.HEADER_HEIGHT, self.w, config.HEADER_HEIGHT,
            fill=config.PANEL_BORDER, width=1, tags="header"
        )
        cy = config.HEADER_HEIGHT // 2

        # PERBAIKAN: Ubah warna menjadi putih agar terbaca
        self.canvas.create_text(
            16, cy, text="RadarRC", anchor="w",
            fill="#ffffff",
            font=("Helvetica", 15, "bold"), tags="header"
        )

        # PERBAIKAN: Geser posisi X titik hijau dan teks ke kanan agar tidak menabrak
        self.canvas.create_oval(
            115, cy - 3, 121, cy + 3,
            fill="#2ecc71", outline="", tags="header"
        )
        self.canvas.create_text(
            129, cy, text="ATC24 LIVE", anchor="w",
            fill=config.TEXT_DIM, font=("Helvetica", 10), tags="header"
        )

        # === TAMBAHKAN KODE INI UNTUK MENGGAMBAR TOMBOL ===
        btn_x2 = self.w - 180
        btn_x1 = btn_x2 - 100
        self.canvas.create_rectangle(
            btn_x1, cy - 12, btn_x2, cy + 12,
            fill="#2ecc71", outline="", tags=("header", "btn_chat_gen")
        )
        self.canvas.create_text(
            (btn_x1 + btn_x2) // 2, cy,
            text="💬 TEXT", fill="#0a1628",
            font=("Helvetica", 9, "bold"), tags=("header", "btn_chat_gen")
        )
        # ===================================================

        now_str = time.strftime("%H:%M:%S")
        self.canvas.create_text(
            self.w - 16, cy,
            text=f"{now_str}    {len(self._data)} aircraft",
            anchor="e", fill=config.TEXT_COLOR,
            font=("Helvetica", 10), tags="header"
        )

        now_str = time.strftime("%H:%M:%S")
        self.canvas.create_text(
            self.w - 16, cy,
            text=f"{now_str}    {len(self._data)} aircraft",
            anchor="e", fill=config.TEXT_COLOR,
            font=("Helvetica", 10), tags="header"
        )

    def _draw_footer(self):
        self.canvas.delete("footer")
        y0 = self.h - config.FOOTER_HEIGHT
        self.canvas.create_rectangle(
            0, y0, self.w, self.h,
            fill=config.CARD_BG, outline="", tags="footer"
        )
        self.canvas.create_line(
            0, y0, self.w, y0,
            fill=config.PANEL_BORDER, width=1, tags="footer"
        )
        hints = "Drag Pan    Scroll Zoom    R Autofit    M Map    Esc Deselect"
        self.canvas.create_text(
            16, y0 + config.FOOTER_HEIGHT // 2,
            text=hints, anchor="w",
            fill=config.TEXT_DIM, font=("Helvetica", 9), tags="footer"
        )
        self.canvas.create_text(
            self.w - 16, y0 + config.FOOTER_HEIGHT // 2,
            text=f"Zoom {self.zoom:.2f}x", anchor="e",
            fill=config.TEXT_COLOR, font=("Helvetica", 9, "bold"), tags="footer"
        )

    def _draw_sidebar(self):
        self.canvas.delete("sidebar")
        sb_w = config.SIDEBAR_WIDTH
        sb_top = config.HEADER_HEIGHT
        sb_bot = self.h - config.FOOTER_HEIGHT

        self.canvas.create_rectangle(
            0, sb_top, sb_w, sb_bot,
            fill=config.PANEL_BG, outline="", tags="sidebar"
        )
        self.canvas.create_line(
            sb_w, sb_top, sb_w, sb_bot,
            fill=config.PANEL_BORDER, width=1, tags="sidebar"
        )

        sh_h = 30
        self.canvas.create_rectangle(
            0, sb_top, sb_w, sb_top + sh_h,
            fill=config.SECTION_BG, outline="", tags="sidebar"
        )
        self.canvas.create_text(
            14, sb_top + sh_h // 2, text="AIRCRAFT", anchor="w",
            fill="#ffffff", font=("Helvetica", 11, "bold"), tags="sidebar"
        )
        self.canvas.create_text(
            sb_w - 14, sb_top + sh_h // 2, text=f"{len(self._data)}", anchor="e",
            fill="#ffffff", font=("Helvetica", 11, "bold"), tags="sidebar"
        )

        try:
            self.search_entry.lift()
        except Exception:
            pass
        if not self.search_var.get():
            self.canvas.create_text(
                16, sb_top + sh_h + 18,
                text="Search callsign...",
                anchor="w", fill=config.TEXT_DIM,
                font=("Helvetica", 10), tags="sidebar"
            )

        list_top = sb_top + sh_h + 36
        list_bot = sb_bot - 4
        list_height = list_bot - list_top

        filtered = self._get_filtered_data()
        sorted_ac = sorted(
            filtered.items(),
            key=lambda kv: kv[1].get("altitude", 0),
            reverse=True
        )

        if not sorted_ac:
            self.canvas.create_text(
                sb_w // 2, list_top + 30, text="No match",
                fill=config.TEXT_DIM,
                font=("Helvetica", 10, "italic"), tags="sidebar"
            )
            self.sidebar_scroll = 0
            return

        item_h = 44
        total_h = len(sorted_ac) * item_h
        max_scroll = max(0, total_h - list_height)
        self.sidebar_scroll = max(0, min(self.sidebar_scroll, max_scroll))
        y_start = list_top - self.sidebar_scroll

        for i, (cs, info) in enumerate(sorted_ac):
            y = y_start + i * item_h
            if y + item_h < list_top:
                continue
            if y > list_bot:
                break
            item_y = max(y, list_top)
            item_bottom = min(y + item_h - 4, list_bot)
            if item_bottom - item_y < 5:
                continue

            alt = info.get("altitude", 0)
            fl = int(alt / 100) if alt else 0
            on_ground = info.get("isOnGround", False)
            color = self._get_color(alt, on_ground)
            is_sel = (cs == self.selected_callsign)
            is_match = self._is_matched(cs)
            has_plan = bool(info.get("plan_departing"))
            is_hover = (cs == self._hovered_callsign)

            if is_sel:
                bg = config.SELECTED_BG
            elif is_hover:
                bg = config.HOVER_BG
            elif is_match:
                bg = "#e0f0e0"
            else:
                bg = config.CARD_BG

            self.canvas.create_rectangle(
                6, item_y + 2, sb_w - 6, item_bottom,
                fill=bg, outline=config.PANEL_BORDER, width=1,
                tags="sidebar"
            )
            self.canvas.create_rectangle(
                6, item_y + 2, 10, item_bottom,
                fill=color, outline="", tags="sidebar"
            )

            tc = config.SECTION_BG if is_sel else config.TEXT_COLOR
            if is_match and not is_sel:
                tc = "#1e7a3e"

            prefix = "*  " if has_plan else ""
            self.canvas.create_text(
                16, y + 14, text=prefix + cs, anchor="w",
                fill=tc, font=("Helvetica", 11, "bold"), tags="sidebar"
            )

            airline = get_airline_name(cs)
            ac_type = info.get("aircraftType", "?")
            sub = f"{airline}  -  {ac_type}"
            if len(sub) > 28:
                sub = sub[:27] + "..."
            self.canvas.create_text(
                16, y + 30, text=sub, anchor="w",
                fill=config.TEXT_DIM, font=("Helvetica", 8), tags="sidebar"
            )
            self.canvas.create_text(
                sb_w - 14, y + 14, text=f"FL{fl:03d}", anchor="e",
                fill=color, font=("Helvetica", 11, "bold"), tags="sidebar"
            )
            self.canvas.create_text(
                sb_w - 14, y + 30, text=f"{int(alt)}m", anchor="e",
                fill=config.TEXT_DIM, font=("Helvetica", 8), tags="sidebar"
            )

            tag = f"ac_{cs}"
            self.canvas.create_rectangle(
                6, item_y + 2, sb_w - 6, item_bottom,
                fill="", outline="", tags=("sidebar", tag)
            )
            self.canvas.tag_bind(
                tag, "<Button-1>",
                lambda e, c=cs: self._select_from_sidebar(c)
            )
            self.canvas.tag_bind(
                tag, "<Enter>",
                lambda e, c=cs: self._set_hovered(c)
            )
            self.canvas.tag_bind(
                tag, "<Leave>",
                lambda e: self._set_hovered(None)
            )

        if max_scroll > 0:
            track_x = sb_w - 4
            thumb_h = max(20, int(list_height * list_height / total_h))
            thumb_y = list_top + int((self.sidebar_scroll / max_scroll) * (list_height - thumb_h))
            self.canvas.create_rectangle(
                track_x, list_top, track_x + 3, list_bot,
                fill="#d0d8e0", outline="", tags="sidebar"
            )
            self.canvas.create_rectangle(
                track_x, thumb_y, track_x + 3, thumb_y + thumb_h,
                fill=config.SECTION_BG, outline="", tags="sidebar"
            )

        # --- TAMBAHKAN KODE INI DI BARIS PALING BAWAH FUNGSI ---
        # Pastikan header, footer, dan kotak pencarian selalu di layer terdepan
        self.canvas.tag_raise("header")
        self.canvas.tag_raise("footer")
        try:
            self.search_entry.lift()
        except Exception:
            pass

    def _set_hovered(self, callsign):
        if self._hovered_callsign != callsign:
            self._hovered_callsign = callsign
            self._redraw()

    def _select_from_sidebar(self, callsign):
        self.selected_callsign = callsign
        self.panel_scroll = 0
        info = self._data.get(callsign)
        if info:
            self._dyn_center = (info.get("x", 0), info.get("y", 0))
        self._redraw()

    def _draw_info_panel(self):
        self.canvas.delete("panel")
        self.canvas.delete("aircraft_image")

        if not self.selected_callsign:
            return
        info = self._data.get(self.selected_callsign)
        if not info:
            return

        alt = info.get("altitude", 0)
        hdg = info.get("heading", 0)
        spd = info.get("speed", 0)
        gs = info.get("groundSpeed", 0)
        fl = int(alt / 100) if alt else 0
        on_ground = info.get("isOnGround", False)
        pilot_name = info.get("playerName", "?")

        dep = info.get("plan_departing", "")
        arr = info.get("plan_arriving", "")
        route = info.get("plan_route", "")
        rules = info.get("plan_flightrules", "")
        has_route = bool(dep and arr)

        vs = 0
        if self.selected_callsign in self._prev_data:
            pa = self._prev_data[self.selected_callsign].get("altitude", alt)
            dt = max(time.time() - self._prev_time, 0.001)
            vs = (alt - pa) / dt

        img_path = self._find_aircraft_image(
            info.get("aircraftType", ""), self.selected_callsign
        )
        has_image = img_path is not None

        pw = 340
        px = self.w - pw - 12
        py = config.HEADER_HEIGHT + 12

        header_h = 48
        img_h = 140 if has_image else 0
        route_h = 90 if has_route else 0
        sec_head_h = 26
        row_h = 44

        sections = [
            ("AIRCRAFT INFORMATION", [
                ("AIRCRAFT TYPE", info.get("aircraftType", "?")[:20], config.TEXT_COLOR),
                ("AIRLINE", get_airline_name(self.selected_callsign)[:20], "#4ade80"),
            ]),
            ("FLIGHT STATUS", [
                ("STATUS", "AIRBORNE" if not on_ground else "ON GROUND",
                 "#4ade80" if not on_ground else "#60a5fa"),
                ("FLIGHT RULES", rules or "-", "#60a5fa"),
            ]),
            ("TELEMETRY", [
                ("BAROMETRIC ALT", f"{int(alt)} m  (FL{fl:03d})",
                 self._get_color(alt, on_ground)),
                ("VERTICAL SPEED", f"{vs:+.1f} m/s",
                 "#4ade80" if vs > 0.5 else "#f87171" if vs < -0.5 else config.TEXT_COLOR),
                ("FLIGHT LEVEL", f"FL{fl:03d}", self._get_color(alt, on_ground)),
                ("HEADING", f"{hdg:03.0f} deg", config.TEXT_COLOR),
            ]),
            ("SPEED", [
                ("GROUND SPEED", f"{int(gs)} kt", config.TEXT_COLOR),
                ("TRUE AIRSPEED", f"{int(spd)} kt", config.TEXT_COLOR),
            ]),
            ("PILOT", [
                ("PLAYER NAME", pilot_name[:20], "#60a5fa"),
                ("CALLSIGN", self.selected_callsign[:20], config.TEXT_COLOR),
            ]),
        ]

        content_h = header_h
        if has_image:
            content_h += img_h + 8
        if has_route:
            content_h += route_h + 8
        for _, rows in sections:
            content_h += sec_head_h + ((len(rows) + 1) // 2) * row_h + 4

        max_h = self.h - py - config.FOOTER_HEIGHT - 8
        visible_h = min(content_h, max_h)
        need_scroll = content_h > max_h
        max_scroll = max(0, content_h - max_h)
        self.panel_scroll = max(0, min(self.panel_scroll, max_scroll))

        self._create_rounded_rect(
            px, py, px + pw, py + visible_h, radius=15,
            fill=config.CARD_BG, outline=config.PANEL_BORDER, width=1,
            tags="panel"
        )

        y = py - self.panel_scroll

        airline_icao = get_airline_icao(self.selected_callsign)
        ac_type = info.get("aircraftType", "?")
# ==== Outer panel frame (Sudut Tajam Biasa) ====
        self.canvas.create_rectangle(
            px, py, px + pw, py + visible_h,
            fill=config.CARD_BG, outline=config.PANEL_BORDER, width=1,
            tags="panel"
        )

        y = py - self.panel_scroll

        # ==== Header (yellow accent) ====
        airline_icao = get_airline_icao(self.selected_callsign)
        ac_type = info.get("aircraftType", "?")

        self.canvas.create_rectangle(
            px + 4, y + 4, px + pw - 4, y + header_h,
            fill=config.ACCENT_COLOR, outline="", tags="panel"
        )
        # PERBAIKAN TEKS: Koordinat Y diturunkan ke y + 22 (sebelumnya y + 16)
        self.canvas.create_text(
            px + 14, y + 22, text=self.selected_callsign, anchor="w",
            fill="#1a2733", font=("Helvetica", 16, "bold"), tags="panel"
        )
        type_display = ac_type if len(ac_type) <= 26 else ac_type[:25] + "..."
        # PERBAIKAN TEKS: Koordinat Y diturunkan ke y + 38 (sebelumnya y + 34)
        self.canvas.create_text(
            px + 14, y + 38, text=f"{airline_icao}   {type_display}", anchor="w",
            fill="#4a3a10", font=("Helvetica", 10, "bold"), tags="panel"
        )
        y += header_h

        if has_image:
            card_x1 = px + 6
            card_y1 = y + 4
            card_x2 = px + pw - 6
            card_y2 = y + 4 + img_h
            self.canvas.create_rectangle(
                card_x1, card_y1, card_x2, card_y2,
                fill="#0a1628", outline=config.PANEL_BORDER, width=1,
                tags=("panel", "aircraft_image")
            )
            photo = self._load_aircraft_image(
                img_path, (card_x2 - card_x1) - 4, (card_y2 - card_y1) - 4
            )
            if photo:
                self._current_photo = photo
                self.canvas.create_image(
                    (card_x1 + card_x2) // 2, (card_y1 + card_y2) // 2,
                    image=photo, tags=("panel", "aircraft_image")
                )
            y += img_h + 8

        if has_route:
            self.canvas.create_rectangle(
                px + 4, y, px + pw - 4, y + route_h,
                fill=config.HOVER_BG, outline="", tags="panel"
            )
            self.canvas.create_text(
                px + 18, y + 30, text=dep, anchor="w",
                fill=config.TEXT_COLOR, font=("Helvetica", 24, "bold"), tags="panel"
            )
            self.canvas.create_text(
                px + 18, y + 54, text=get_airport_name(dep), anchor="w",
                fill=config.TEXT_DIM, font=("Helvetica", 9), tags="panel"
            )
            cx_icon = px + pw // 2
            cy_icon = y + 38
            self.canvas.create_oval(
                cx_icon - 14, cy_icon - 14, cx_icon + 14, cy_icon + 14,
                fill=config.SECTION_BG, outline="", tags="panel"
            )
            self.canvas.create_text(
                cx_icon, cy_icon, text=">",
                fill="#ffffff", font=("Helvetica", 14, "bold"), tags="panel"
            )
            self.canvas.create_text(
                px + pw - 18, y + 30, text=arr, anchor="e",
                fill=config.TEXT_COLOR, font=("Helvetica", 24, "bold"), tags="panel"
            )
            self.canvas.create_text(
                px + pw - 18, y + 54, text=get_airport_name(arr), anchor="e",
                fill=config.TEXT_DIM, font=("Helvetica", 9), tags="panel"
            )
            if route:
                rd = route if len(route) <= 48 else route[:47] + "..."
                self.canvas.create_text(
                    px + 18, y + 76, text=rd, anchor="w",
                    fill="#60a5fa", font=("Helvetica", 8), tags="panel"
                )
            y += route_h + 4

        for sec_name, rows in sections:
            self.canvas.create_rectangle(
                px + 4, y, px + pw - 4, y + sec_head_h,
                fill=config.SECTION_BG, outline="", tags="panel"
            )
            self.canvas.create_text(
                px + 14, y + sec_head_h // 2, text=sec_name, anchor="w",
                fill="#ffffff", font=("Helvetica", 10, "bold"), tags="panel"
            )
            y += sec_head_h

            col_w = pw // 2
            for i, (label, value, vc) in enumerate(rows):
                col = i % 2
                row_idx = i // 2
                cx = px + col * col_w
                cy = y + row_idx * row_h

                if row_idx % 2 == 0:
                    self.canvas.create_rectangle(
                        cx + 4, cy, cx + col_w - 4, cy + row_h,
                        fill=config.PANEL_BG, outline="", tags="panel"
                    )

                self.canvas.create_text(
                    cx + 14, cy + 12, text=label, anchor="w",
                    fill=config.TEXT_DIM, font=("Helvetica", 8), tags="panel"
                )
                tid = self.canvas.create_text(
                    cx + 14, cy + 30, text=value, anchor="w",
                    fill=vc, font=("Helvetica", 12, "bold"), tags="panel"
                )
                if label in ("PLAYER NAME", "CALLSIGN"):
                    self.canvas.tag_bind(
                        tid, "<Button-1>",
                        lambda e, n=value: self._copy_to_clipboard(n)
                    )
            y += ((len(rows) + 1) // 2) * row_h + 4

        if need_scroll:
            bar_x = px + pw - 6
            bar_top = py + 4
            bar_bot = py + visible_h - 4
            bar_h = bar_bot - bar_top
            thumb_h = max(24, int(bar_h * visible_h / content_h))
            if max_scroll > 0:
                thumb_y = bar_top + int((self.panel_scroll / max_scroll) * (bar_h - thumb_h))
            else:
                thumb_y = bar_top
            self.canvas.create_rectangle(
                bar_x, bar_top, bar_x + 4, bar_bot,
                fill=config.PANEL_BG, outline="", tags="panel"
            )
            self.canvas.create_rectangle(
                bar_x, thumb_y, bar_x + 4, thumb_y + thumb_h,
                fill=config.SECTION_BG, outline="", tags="panel"
            )

    def _redraw(self):
        self._draw_map()
        self._draw_grid()
        self._draw_trails()
        self._draw_planes()
        self._draw_sidebar()
        self._draw_info_panel()
        self._draw_header()
        self._draw_footer()
        try:
            self.search_entry.lift()
        except Exception:
            pass


    # ================================================================
    # PUBLIC API & RENDER ENGINE (OPTIMIZED)
    # ================================================================
    def update(self, aircraft_data):
        self._prev_data = self._data
        self._prev_time = time.time()
        self._data = aircraft_data

        if not self._fitted and aircraft_data:
            self._autofit()
            self._fitted = True

        self._update_trails()

        # === OPTIMASI SUPER ANTI-LAG ===
        # Membatasi refresh rate ke 10 FPS (100ms) agar CPU tidak kewalahan
        # menerima spam data dari server WebSocket ATC24.
        if not getattr(self, '_render_scheduled', False):
            self._render_scheduled = True
            # Tunda render selama 100ms, lalu jalankan _render_dynamic_elements
            self.parent.after(100, self._render_dynamic_elements)

    def _render_dynamic_elements(self):
        # Reset jadwal render
        self._render_scheduled = False

        # Jika sedang sibuk nge-zoom atau nge-drag peta, abaikan update data
        # agar pergerakan mouse tetap instan dan mulus!
        if self._zoom_timer is not None or self._drag_moved:
            return

        # HANYA gambar elemen yang berubah (JANGAN panggil _draw_map di sini!)
        self._draw_trails()
        self._draw_planes()
        self._draw_sidebar()
        self._draw_info_panel()
        self._draw_header()
        self._draw_footer()

        try:
            self.search_entry.lift()
        except Exception:
            pass
