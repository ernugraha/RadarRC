# frontend/map_renderer.py
"""
Memuat file SVG peta PTFS dan menggambar path-nya di canvas tkinter.
Konversi: 1px di SVG = 100 studs di game.
Mendukung elemen <path> dan <image> (PNG embedded/eksternal).
"""

import re
import os
import xml.etree.ElementTree as ET
import base64
import io
from PIL import Image

# Matikan batas ukuran gambar agar peta PTFS raksasa bisa dimuat
Image.MAX_IMAGE_PIXELS = None

SVG_PX_TO_STUDS = 100.0


class MapRenderer:
    def __init__(self, maps_dir="assets/maps"):
        self.maps_dir = maps_dir
        self.layers = {}
        self.images = {}

    def load_all(self):
        if not os.path.isdir(self.maps_dir):
            print(f"[Map] Folder not found: {self.maps_dir}")
            return
        for fname in os.listdir(self.maps_dir):
            if not fname.endswith(".svg"):
                continue
            name = fname[:-4]
            path = os.path.join(self.maps_dir, fname)
            try:
                polylines, images = self._parse_svg(path)
                self.layers[name] = polylines
                self.images[name] = images

                total_pts = sum(len(p) for p in polylines)
                print(f"[Map] {name}: {len(polylines)} path, {total_pts} titik, {len(images)} gambar")
            except Exception as e:
                print(f"[Map] Failed to load {fname}: {e}")

    def _parse_svg(self, svg_path):
        tree = ET.parse(svg_path)
        root = tree.getroot()
        polylines = []
        images = []

        for elem in root.iter():
            if elem.tag.endswith("path"):
                d = elem.get("d")
                if not d:
                    continue

                # Menggunakan logika baru yang mengembalikan list of subpaths
                subpaths = self._parse_path_d(d)
                if subpaths:
                    polylines.extend(subpaths)

            elif elem.tag.endswith("image"):
                x = float(elem.get("x", 0))
                y = float(elem.get("y", 0))
                w = float(elem.get("width", 0))
                h = float(elem.get("height", 0))

                href = elem.get("href")
                if not href:
                    href = elem.get("{http://www.w3.org/1999/xlink}href")

                if href:
                    img_obj = self._parse_image_href(href, svg_path)
                    if img_obj:
                        target_w = int(w * SVG_PX_TO_STUDS)
                        target_h = int(h * SVG_PX_TO_STUDS)

                        if target_w > 0 and target_h > 0:
                            images.append({
                                "x": x * SVG_PX_TO_STUDS,
                                "y": y * SVG_PX_TO_STUDS,
                                "w": target_w,
                                "h": target_h,
                                "image": img_obj
                            })

        return polylines, images

    def _parse_image_href(self, href, svg_path):
        """Membaca href gambar, bisa berupa Base64 embedded atau path file eksternal."""
        try:
            if href.startswith("data:image"):
                idx = href.find("base64,")
                if idx != -1:
                    b64_data = href[idx+7:]
                    img_data = base64.b64decode(b64_data)
                    return Image.open(io.BytesIO(img_data)).convert("RGBA")
            else:
                base_dir = os.path.dirname(svg_path)
                img_path = os.path.join(base_dir, href)
                if os.path.isfile(img_path):
                    return Image.open(img_path).convert("RGBA")
        except Exception as e:
            print(f"[Map] Gagal memuat gambar dari SVG: {e}")
        return None

    def _parse_path_d(self, d):
        """
        Parse atribut 'd' dari path SVG. Mendukung perintah:
        M/m, L/l, H/h, V/v, C/c, S/s, Q/q, T/t, A/a, Z/z.
        """
        token_pattern = re.compile(
            r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)"
        )
        tokens = []
        for m in token_pattern.finditer(d):
            if m.group(1):
                tokens.append(m.group(1))
            else:
                tokens.append(m.group(2))

        subpaths = []
        pts = []
        i = 0
        cur_x, cur_y = 0.0, 0.0
        start_x, start_y = 0.0, 0.0
        last_cmd = None

        def num(idx):
            if idx >= len(tokens):
                return None
            try:
                return float(tokens[idx])
            except (ValueError, TypeError):
                return None

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
                # "Angkat pena": Simpan garis yang sudah ada sebelumnya
                if len(pts) > 0:
                    subpaths.append(pts)
                    pts = []

                x = num(i); y = num(i + 1)
                if x is None or y is None:
                    break
                if cmd == "m":
                    cur_x += x
                    cur_y += y
                else:
                    cur_x, cur_y = x, y
                start_x, start_y = cur_x, cur_y
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 2
                last_cmd = "L" if cmd == "M" else "l"

            elif cmd in ("L", "l"):
                x = num(i); y = num(i + 1)
                if x is None or y is None:
                    break
                if cmd == "l":
                    cur_x += x
                    cur_y += y
                else:
                    cur_x, cur_y = x, y
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 2
                last_cmd = cmd

            elif cmd in ("H", "h"):
                x = num(i)
                if x is None:
                    break
                if cmd == "h":
                    cur_x += x
                else:
                    cur_x = x
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 1
                last_cmd = cmd

            elif cmd in ("V", "v"):
                y = num(i)
                if y is None:
                    break
                if cmd == "v":
                    cur_y += y
                else:
                    cur_y = y
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 1
                last_cmd = cmd

            elif cmd in ("C", "c"):
                vals = [num(i + k) for k in range(6)]
                if any(v is None for v in vals):
                    break
                if cmd == "c":
                    end_x = cur_x + vals[4]
                    end_y = cur_y + vals[5]
                else:
                    end_x, end_y = vals[4], vals[5]
                cur_x, cur_y = end_x, end_y
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 6
                last_cmd = cmd

            elif cmd in ("S", "s"):
                vals = [num(i + k) for k in range(4)]
                if any(v is None for v in vals):
                    break
                if cmd == "s":
                    end_x = cur_x + vals[2]
                    end_y = cur_y + vals[3]
                else:
                    end_x, end_y = vals[2], vals[3]
                cur_x, cur_y = end_x, end_y
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 4
                last_cmd = cmd

            elif cmd in ("Q", "q"):
                vals = [num(i + k) for k in range(4)]
                if any(v is None for v in vals):
                    break
                if cmd == "q":
                    end_x = cur_x + vals[2]
                    end_y = cur_y + vals[3]
                else:
                    end_x, end_y = vals[2], vals[3]
                cur_x, cur_y = end_x, end_y
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 4
                last_cmd = cmd

            elif cmd in ("T", "t"):
                vals = [num(i + k) for k in range(2)]
                if any(v is None for v in vals):
                    break
                if cmd == "t":
                    cur_x += vals[0]
                    cur_y += vals[1]
                else:
                    cur_x, cur_y = vals[0], vals[1]
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 2
                last_cmd = cmd

            elif cmd in ("A", "a"):
                vals = [num(i + k) for k in range(7)]
                if any(v is None for v in vals):
                    break
                if cmd == "a":
                    cur_x += vals[5]
                    cur_y += vals[6]
                else:
                    cur_x, cur_y = vals[5], vals[6]
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 7
                last_cmd = cmd

            elif cmd in ("Z", "z"):
                cur_x, cur_y = start_x, start_y
                pts.append((cur_x * SVG_PX_TO_STUDS, cur_y * SVG_PX_TO_STUDS))
                i += 0
                last_cmd = cmd
                if i < len(tokens) and not (isinstance(tokens[i], str) and tokens[i].isalpha()):
                    i += 1
            else:
                i += 1
                continue

        # Simpan subpath terakhir sebelum return
        if len(pts) > 0:
            subpaths.append(pts)

        return subpaths
