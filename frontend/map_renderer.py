# frontend/map_renderer.py

import re
import os
import xml.etree.ElementTree as ET
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QBrush, QColor
from PySide6.QtCore import Qt

class MapRenderer:
    def __init__(self, maps_dir="assets/maps"):
        self.maps_dir = maps_dir

    def load_layer(self, filename, color=QColor(100, 100, 100, 150), fill_color=None, stroke_width=1.0):
        """Memuat file SVG dan mengubahnya menjadi QGraphicsPathItem."""
        path = os.path.join(self.maps_dir, filename)
        if not os.path.exists(path):
            print(f"[Map] File not found: {path}")
            return []

        try:
            items = self._parse_svg_to_paths(path, color, fill_color, stroke_width)
            print(f"[Map] Successfully loaded {filename} ({len(items)} paths)")
            return items
        except Exception as e:
            print(f"[Map] Failed to load {filename}: {e}")
            return []

    def _parse_svg_to_paths(self, svg_path, color, fill_color, stroke_width):
        tree = ET.parse(svg_path)
        root = tree.getroot()
        items = []

        for elem in root.iter():
            if elem.tag.endswith("path"):
                d = elem.get("d")
                if not d:
                    continue

                qpath = QPainterPath()
                self._parse_path_d(d, qpath)

                if not qpath.isEmpty():
                    item = QGraphicsPathItem(qpath)

                    # Atur styling
                    pen = QPen(color)
                    pen.setWidthF(stroke_width)
                    pen.setCosmetic(True) # Garis tetap tebal walau di-zoom
                    item.setPen(pen)

                    if fill_color:
                        item.setBrush(QBrush(fill_color))
                    else:
                        item.setBrush(Qt.NoBrush)

                    items.append(item)

        return items

    def _parse_path_d(self, d, qpath):
        """Parse atribut 'd' dari path SVG dan masukkan ke QPainterPath."""
        token_pattern = re.compile(
            r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)"
        )
        tokens = []
        for m in token_pattern.finditer(d):
            if m.group(1):
                tokens.append(m.group(1))
            else:
                tokens.append(m.group(2))

        i = 0
        cur_x, cur_y = 0.0, 0.0
        start_x, start_y = 0.0, 0.0
        last_cmd = None

        def num(idx):
            if idx >= len(tokens): return None
            try: return float(tokens[idx])
            except (ValueError, TypeError): return None

        while i < len(tokens):
            t = tokens[i]
            if isinstance(t, str) and t.isalpha():
                cmd = t
                i += 1
            else:
                cmd = last_cmd
                if cmd is None:
                    i += 1
                    continue

            if cmd in ("M", "m"):
                x, y = num(i), num(i + 1)
                if x is None or y is None: break
                if cmd == "m":
                    cur_x += x; cur_y += y
                else:
                    cur_x, cur_y = x, y
                start_x, start_y = cur_x, cur_y
                qpath.moveTo(cur_x, cur_y)
                i += 2
                last_cmd = "L" if cmd == "M" else "l"

            elif cmd in ("L", "l"):
                x, y = num(i), num(i + 1)
                if x is None or y is None: break
                if cmd == "l":
                    cur_x += x; cur_y += y
                else:
                    cur_x, cur_y = x, y
                qpath.lineTo(cur_x, cur_y)
                i += 2
                last_cmd = cmd

            elif cmd in ("H", "h"):
                x = num(i)
                if x is None: break
                if cmd == "h": cur_x += x
                else: cur_x = x
                qpath.lineTo(cur_x, cur_y)
                i += 1
                last_cmd = cmd

            elif cmd in ("V", "v"):
                y = num(i)
                if y is None: break
                if cmd == "v": cur_y += y
                else: cur_y = y
                qpath.lineTo(cur_x, cur_y)
                i += 1
                last_cmd = cmd

            elif cmd in ("C", "c"):
                vals = [num(i + k) for k in range(6)]
                if any(v is None for v in vals): break
                if cmd == "c":
                    c1x, c1y = cur_x + vals[0], cur_y + vals[1]
                    c2x, c2y = cur_x + vals[2], cur_y + vals[3]
                    end_x, end_y = cur_x + vals[4], cur_y + vals[5]
                else:
                    c1x, c1y, c2x, c2y, end_x, end_y = vals
                qpath.cubicTo(c1x, c1y, c2x, c2y, end_x, end_y)
                cur_x, cur_y = end_x, end_y
                i += 6
                last_cmd = cmd

            elif cmd in ("Q", "q"):
                vals = [num(i + k) for k in range(4)]
                if any(v is None for v in vals): break
                if cmd == "q":
                    cx, cy = cur_x + vals[0], cur_y + vals[1]
                    end_x, end_y = cur_x + vals[2], cur_y + vals[3]
                else:
                    cx, cy, end_x, end_y = vals
                qpath.quadTo(cx, cy, end_x, end_y)
                cur_x, cur_y = end_x, end_y
                i += 4
                last_cmd = cmd

            elif cmd in ("Z", "z"):
                qpath.closeSubpath()
                cur_x, cur_y = start_x, start_y
                i += 0
                last_cmd = cmd
                if i < len(tokens) and not (isinstance(tokens[i], str) and tokens[i].isalpha()):
                    i += 1
            else:
                # Untuk kurva S, T, A yang kompleks, kita lewati dulu
                # (kebanyakan peta 24RC hanya pakai M, L, C, Z)
                i += 1
                continue
