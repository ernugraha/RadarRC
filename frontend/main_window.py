# frontend/main_window.py

    def update_aircraft(self, data_dict):
        self.current_data = data_dict
        active_callsigns = set(data_dict.keys())

        # 1. Tambah/Update Pesawat
        for callsign, info in data_dict.items():
            if "x" not in info or "y" not in info: continue
            x, y = info["x"], info["y"]
            heading = info.get("heading", 0)
            alt = info.get("altitude", 0)
            ac_type = info.get("aircraftType", "")

            if callsign not in self.aircraft_items:
                plane = AircraftItem(callsign, ac_type)
                self.scene.addItem(plane)
                self.aircraft_items[callsign] = plane

            self.aircraft_items[callsign].update_data(x, y, heading, ac_type)
            self.trail_manager.add_point(callsign, x, y, alt)

        # 2. HAPUS PESAWAT HANTU (Yang sudah keluar dari server)
        for callsign in list(self.aircraft_items.keys()):
            if callsign not in active_callsigns:
                item = self.aircraft_items.pop(callsign)
                self.scene.removeItem(item)

        # 3. Sinkronisasi Trail
        self.trail_manager.sync_to_db()
        self.trail_manager.cleanup(active_callsigns)

        # 4. Perbarui Trail yang sedang aktif dipilih
        selected_items = self.scene.selectedItems()
        if selected_items and isinstance(selected_items[0], AircraftItem):
            selected_cs = selected_items[0].callsign

            # Jika pesawat yang dipilih tiba-tiba hilang (mendarat/leave)
            if selected_cs not in active_callsigns:
                self.scene.clearSelection() # Memicu penutupan panel info otomatis
                if self.current_trail_item:
                    self.scene.removeItem(self.current_trail_item)
                    self.current_trail_item = None
            elif self.current_trail_item:
                trail_points = self.trail_manager.get_trail(selected_cs)
                self.current_trail_item.set_points(trail_points)

        # 5. Update Sidebar
        now = time.time()
        if now - self.last_sidebar_update > 1.0:
            self.sidebar.update_data(data_dict)
            self.last_sidebar_update = now
