# frontend/chat_generator.py
import tkinter as tk
from tkinter import ttk

# ==========================================
# PILOT CHEAT SHEET TEMPLATES
# ==========================================
TEMPLATES = {
    "1. DEPARTURE (Ground/Tower)": [
        ("Req IFR Clearance", "{AIRPORT} Ground, {CALLSIGN}, stand {GATE}, with information {ATIS}, request IFR clearance to {DEST}."),
        ("Req Startup", "{AIRPORT} Ground, {CALLSIGN}, request startup."),
        ("Req Startup & Push", "{AIRPORT} Ground, {CALLSIGN}, request startup and pushback."),
        ("Req Pushback", "{AIRPORT} Ground, {CALLSIGN}, request pushback."),
        ("Ready to Taxi", "{AIRPORT} Ground, {CALLSIGN}, ready to taxi."),
        ("Req Taxi to RWY", "{AIRPORT} Ground, {CALLSIGN}, ready to taxi to runway {RWY}."),
        ("Req Taxi Instruct.", "{AIRPORT} Ground, {CALLSIGN}, request taxi instructions."),
        ("Holding Short", "{AIRPORT} Tower, {CALLSIGN}, holding short runway {RWY}."),
        ("Ready for Depart.", "{AIRPORT} Tower, {CALLSIGN}, holding short runway {RWY}, ready for departure."),
    ],
    "2. ENROUTE (Center)": [
        ("Passing Altitude", "Center, {CALLSIGN}, passing {MISC}, climbing {ALT}."),
        ("Req Climb", "Center, {CALLSIGN}, request climb to {ALT}."),
        ("Req Descent", "Center, {CALLSIGN}, request descent to {ALT}."),
        ("Req Heading", "Center, {CALLSIGN}, request heading {HEADING}."),
        ("Req Vectors", "Center, {CALLSIGN}, request vectors to {DEST}."),
        ("Req Speed", "Center, {CALLSIGN}, request speed {SPEED} knots."),
        ("Req Direct", "Center, {CALLSIGN}, request direct {DEST}."),
        ("Req Diff Route", "Center, {CALLSIGN}, request different routing to {DEST}."),
        ("Req Holding", "Center, {CALLSIGN}, request holding."),
    ],
    "3. ARRIVAL (Tower/Ground)": [
        ("Req ILS Approach", "{AIRPORT} Tower, {CALLSIGN}, request ILS approach runway {RWY}."),
        ("Req Visual App.", "{AIRPORT} Tower, {CALLSIGN}, request visual approach runway {RWY}."),
        ("Est. ILS", "{AIRPORT} Tower, {CALLSIGN}, established ILS runway {RWY}."),
        ("5 Mile Final", "{AIRPORT} Tower, {CALLSIGN}, five mile final runway {RWY}."),
        ("Req Landing Clear.", "{AIRPORT} Tower, {CALLSIGN}, final runway {RWY}, request landing clearance."),
        ("Go Around Action", "{AIRPORT} Tower, {CALLSIGN}, going around, request further instructions."),
        ("Runway Vacated", "{AIRPORT} Ground, {CALLSIGN}, runway {RWY} vacated, request taxi to gate."),
        ("At Gate", "{AIRPORT} Ground, {CALLSIGN}, at gate {GATE}."),
    ],
    "4. RESPOND TO ATC (Readback)": [
        ("Readback Clearance", "Cleared to {DEST} via {ROUTE}, expect runway {RWY}, climb and maintain {ALT}, squawk {SQUAWK}, {CALLSIGN}."),
        ("R/B Start & Push", "Startup and pushback approved, {CALLSIGN}."),
        ("R/B Taxi", "Taxi to runway {RWY} via {TAXIWAY}, {CALLSIGN}."),
        ("R/B Hold Short", "Taxi to runway {RWY} via {TAXIWAY}, hold short runway {RWY}, {CALLSIGN}."),
        ("R/B Line Up & Wait", "Runway {RWY}, line up and wait, {CALLSIGN}."),
        ("R/B Cleared Takeoff", "Runway {RWY}, cleared for takeoff, {CALLSIGN}."),
        ("R/B Contact Center", "Contact Center {FREQ}, {CALLSIGN}."),
        ("R/B Heading", "Heading {HEADING}, {CALLSIGN}."),
        ("R/B Climb/Descend", "Climb/descend and maintain {ALT}, {CALLSIGN}."),
        ("R/B Speed", "Speed {SPEED} knots, {CALLSIGN}."),
        ("R/B Direct", "Direct {DEST}, {CALLSIGN}."),
        ("R/B Cleared to Land", "Runway {RWY}, cleared to land, {CALLSIGN}."),
        ("R/B Go Around", "Going around, {CALLSIGN}."),
        ("R/B Vacate", "Vacating left/right when able, {CALLSIGN}."),
        ("R/B Taxi to Gate", "Taxi to gate {GATE} via {TAXIWAY}, {CALLSIGN}."),
    ],
    "5. EMERGENCY & MISC": [
        ("Say Again", "Say again, {CALLSIGN}."),
        ("Unable", "Unable, {CALLSIGN}."),
        ("Confirm", "Confirm {MISC}, {CALLSIGN}."),
        ("Radio Check", "Tower, {CALLSIGN}, radio check."),
        ("Req Priority", "Tower, {CALLSIGN}, request priority handling."),
        ("Req Diversion", "Center, {CALLSIGN}, request diversion to {AIRPORT}."),
        ("Unsure Taxiway", "Ground, {CALLSIGN}, we are unsure of our taxi route, request assistance."),
        ("Lost / Unsure Pos", "Center, {CALLSIGN}, unable to determine position, request vectors to {AIRPORT}."),
        ("MAYDAY General", "Mayday, Mayday, Mayday, Tower, {CALLSIGN}, {PROBLEM}, {POSITION}, {ALT}, request immediate landing."),
        ("PAN PAN General", "Pan Pan, Pan Pan, Pan Pan, Tower, {CALLSIGN}, {PROBLEM}, request priority."),
        ("MAYDAY Engine", "Mayday, Mayday, Mayday, Tower, {CALLSIGN}, engine failure, {POSITION}, {ALT}, request immediate landing."),
        ("MAYDAY Fuel", "Mayday, Mayday, Mayday, Tower, {CALLSIGN}, fuel emergency, request immediate landing."),
    ]
}

# ==========================================
# PENJELASAN KOLOM UNTUK PILOT (ENGLISH)
# ==========================================
FIELD_INFO = {
    "{CALLSIGN}": "Aircraft callsign (e.g., SIA-203, Garuda-876)",
    "{AIRPORT}": "Current or departure airport (e.g., IPPH, WIII)",
    "{DEST}": "Destination airport (e.g., IRFD, WSSS)",
    "{RWY}": "Runway number (e.g., 25, 07R)",
    "{ALT}": "Flight altitude (e.g., FL060, 5000)",
    "{HEADING}": "Compass heading 0-360 degrees (e.g., 230, 090)",
    "{SPEED}": "Target speed in knots (e.g., 250, 180)",
    "{GATE}": "Airport gate / parking stand (e.g., 1, A5)",
    "{ROUTE}": "Flight route / SID / STAR",
    "{TAXIWAY}": "Aircraft taxiway (e.g., Alpha, B2)",
    "{SQUAWK}": "4-digit ATC transponder code (e.g., 2000)",
    "{ATIS}": "ATIS weather information letter (e.g., A, B, C)",
    "{FREQ}": "ATC radio frequency (e.g., 118.1)",
    "{PROBLEM}": "Type of emergency problem (e.g., engine failure, medical)",
    "{POSITION}": "Current aircraft position (e.g., 5 miles south)",
    "{MISC}": "Miscellaneous (for passing altitude, confirm rwy, etc.)"
}

class ChatGeneratorWindow(tk.Toplevel):
    def __init__(self, parent, callsign=""):
        super().__init__(parent)
        self.title("Pilot Cheat Sheet Generator")
        self.geometry("640x580")
        self.configure(bg="#0a1628")
        self.resizable(False, False)

        # Variabel Data Penerbangan
        self.vars = {
            "{CALLSIGN}": tk.StringVar(value=callsign),
            "{AIRPORT}": tk.StringVar(value="IPPH"),
            "{DEST}": tk.StringVar(),
            "{RWY}": tk.StringVar(),
            "{ALT}": tk.StringVar(value="FL"),
            "{HEADING}": tk.StringVar(),
            "{SPEED}": tk.StringVar(),
            "{GATE}": tk.StringVar(),
            "{ROUTE}": tk.StringVar(),
            "{TAXIWAY}": tk.StringVar(),
            "{SQUAWK}": tk.StringVar(),
            "{ATIS}": tk.StringVar(),
            "{FREQ}": tk.StringVar(),
            "{PROBLEM}": tk.StringVar(value="engine failure"),
            "{POSITION}": tk.StringVar(value="5 miles south"),
            "{MISC}": tk.StringVar(value="runway 25")
        }

        self._build_ui()

    def _build_ui(self):
        # 1. Top Frame: Input Fields
        top_frame = tk.Frame(self, bg="#0a1628", padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        labels = list(self.vars.keys())
        for i, key in enumerate(labels):
            row = i // 4
            col = i % 4
            label_text = key.strip("{}")
            tk.Label(top_frame, text=label_text, bg="#0a1628", fg="#7ec8ff", font=("Helvetica", 8, "bold")).grid(row=row*2, column=col, sticky="w", padx=5, pady=(5,0))

            ent = tk.Entry(top_frame, textvariable=self.vars[key], bg="#152238", fg="#ffffff", insertbackground="white", relief="flat", highlightbackground="#313244", highlightthickness=1, width=13)
            ent.grid(row=row*2+1, column=col, padx=5, pady=2)
            self.vars[key].trace_add("write", self._update_preview)

            # Event Listener untuk Hover dan Fokus
            def on_hover(event, k=key):
                self.info_label.config(text=f"{k.strip('{}')}: {FIELD_INFO[k]}")

            ent.bind("<Enter>", on_hover)
            ent.bind("<FocusIn>", on_hover)

        # Label Informasi (Dynamic Helper)
        self.info_label = tk.Label(top_frame, text="Hover over an input field to see its description.", bg="#0a1628", fg="#f6c177", font=("Helvetica", 9, "italic"))
        self.info_label.grid(row=8, column=0, columnspan=4, sticky="w", padx=5, pady=(15, 0))

        # 2. Middle Frame: Categories & Templates
        mid_frame = tk.Frame(self, bg="#0a1628", padx=10, pady=5)
        mid_frame.pack(fill=tk.BOTH, expand=True)

        # Category List
        cat_frame = tk.Frame(mid_frame, bg="#0a1628")
        cat_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        tk.Label(cat_frame, text="PHASE / CATEGORY", bg="#0a1628", fg="#a6adc8", font=("Helvetica", 9, "bold")).pack(anchor="w")

        # PERBAIKAN BUG: exportselection=False ditambahkan di sini
        self.cat_list = tk.Listbox(cat_frame, bg="#152238", fg="white", selectbackground="#2ecc71", selectforeground="#0a1628", relief="flat", highlightthickness=0, width=28, font=("Helvetica", 10), exportselection=False)
        self.cat_list.pack(fill=tk.Y, expand=True)
        for cat in TEMPLATES.keys():
            self.cat_list.insert(tk.END, cat)
        self.cat_list.bind("<<ListboxSelect>>", self._on_cat_select)

        # Template List
        tpl_frame = tk.Frame(mid_frame, bg="#0a1628")
        tpl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(tpl_frame, text="MESSAGES", bg="#0a1628", fg="#a6adc8", font=("Helvetica", 9, "bold")).pack(anchor="w")

        # PERBAIKAN BUG: exportselection=False ditambahkan di sini
        self.tpl_list = tk.Listbox(tpl_frame, bg="#152238", fg="white", selectbackground="#4ade80", selectforeground="#0a1628", relief="flat", highlightthickness=0, font=("Helvetica", 10), exportselection=False)
        self.tpl_list.pack(fill=tk.BOTH, expand=True)
        self.tpl_list.bind("<<ListboxSelect>>", self._on_tpl_select)

        # 3. Bottom Frame: Output & Copy
        bot_frame = tk.Frame(self, bg="#0a1628", padx=10, pady=10)
        bot_frame.pack(fill=tk.X)

        tk.Label(bot_frame, text="FINAL TEXT (Ready to Send)", bg="#0a1628", fg="#2ecc71", font=("Helvetica", 9, "bold")).pack(anchor="w")
        self.result_text = tk.Text(bot_frame, height=3, bg="#1e1e2e", fg="#ffffff", font=("Consolas", 11), relief="flat", highlightbackground="#2ecc71", highlightthickness=1)
        self.result_text.pack(fill=tk.X, pady=(5, 10))

        copy_btn = tk.Button(bot_frame, text="COPY TO CLIPBOARD", bg="#2ecc71", fg="#0a1628", font=("Helvetica", 10, "bold"), relief="flat", cursor="hand2", command=self._copy_text)
        copy_btn.pack(ipady=5, ipadx=10)

        self.current_template = ""
        self.cat_list.selection_set(0)
        self._on_cat_select(None)

    def _on_cat_select(self, event):
        if not self.cat_list.curselection(): return

        # PERBAIKAN: Tambahkan [0] untuk mengambil index spesifik
        cat_idx = self.cat_list.curselection()[0]
        cat = self.cat_list.get(cat_idx)

        self.tpl_list.delete(0, tk.END)
        for name, _ in TEMPLATES[cat]:
            self.tpl_list.insert(tk.END, name)

        if self.tpl_list.size() > 0:
            self.tpl_list.selection_set(0)
            self._on_tpl_select(None)

    def _on_tpl_select(self, event):
        if not self.tpl_list.curselection(): return

        cat_sel = self.cat_list.curselection()
        if not cat_sel:
            return

        # PERBAIKAN: Tambahkan [0] di sini juga
        cat = self.cat_list.get(cat_sel[0])
        idx = self.tpl_list.curselection()[0]

        self.current_template = TEMPLATES[cat][idx][1]
        self._update_preview()

    def _update_preview(self, *args):
        text = self.current_template
        for key, var in self.vars.items():
            val = var.get().strip()
            if not val:
                val = ""
            text = text.replace(key, val)

        text = text.replace("  ", " ").replace(" ,", ",").strip()

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)

    def _copy_text(self):
        text = self.result_text.get(1.0, tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

            btn = self.focus_get()
            if isinstance(btn, tk.Button):
                orig_bg = btn.cget("background")
                btn.config(background="#ffffff")
                self.after(150, lambda: btn.config(background=orig_bg))
