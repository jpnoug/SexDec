#!/usr/bin/env python3
"""
Convertisseur Sex Dec de Martine — Interface Tkinter (layout grid)
"""

import sys, os, re, tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from radec_convert import (
    ra_dec2sex, dec_dec2sex,
    period_day2hms, period_hms2day,
    parse_ra, parse_dec, parse_period,
    fmt_ra_sex, fmt_dec_sex,
    fmt_period_hms, fmt_period_day,
)

# ── Palette ────────────────────────────────────────────────────────────────
BG      = "#1a1a1a"
BG2     = "#242424"
BG3     = "#2c2c2c"
ACCENT  = "#c0392b"
ACCENT2 = "#e74c3c"
ACCENT3 = "#6b1710"
OK_COL  = "#f0f0f0"
ERR_COL = "#ff8080"
FG      = "#f0f0f0"
FG2     = "#bbbbbb"
SEP     = "#3a3a3a"
BOX_HL  = "#606060"

FONT_HINT = ("Segoe UI",  10)
FONT_TTL  = ("Segoe UI",  10, "bold")
FONT_MONO = ("Consolas",  12)
FONT_RES  = ("Consolas",  12, "bold")
FONT_BTN  = ("Segoe UI",  10, "bold")

# ── Dimensions fixes ───────────────────────────────────────────────────────
BOX_W   = 300   # largeur px — entrée ET sortie identiques
BOX_H   = 78    # hauteur px
BTN_W   = 100
COL_PAD = 16    # espace entre colonnes

# ── Validation ─────────────────────────────────────────────────────────────
def validate_sexagesimal(h_or_d, m, s, kind="RA"):
    errs = []
    if kind == "RA":
        if not (0 <= h_or_d < 24):
            errs.append(f"Heures RA {h_or_d} invalides [0–23]")
    else:
        if not (0 <= h_or_d <= 90):
            errs.append(f"Degrés DEC {h_or_d} invalides [0–90]")
    if not (0 <= m < 60):
        errs.append(f"Minutes {m} invalides [0–59]")
    if not (0 <= s < 60):
        errs.append(f"Secondes {s:.3f} invalides — max 59.999")
    return errs

def validate_decimal_ra(v):
    return [f"RA {v} h invalide — plage [0–24]"] if not (0 <= v < 24) else []

def validate_decimal_dec(v):
    return [f"DEC {v}° invalide — plage [-90°–+90°]"] if not (-90 <= v <= 90) else []

def validate_period(days):
    return [f"Période négative ({days} j)"] if days < 0 else []

# ── Helpers ────────────────────────────────────────────────────────────────
def copy_clip(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)

def mk_separator(parent, row_idx, colspan=3):
    """Ligne séparatrice horizontale via grid."""
    sep = tk.Frame(parent, bg=SEP, height=1)
    sep.grid(row=row_idx, column=0, columnspan=colspan,
             sticky="ew", padx=8, pady=4)

def mk_section_title(parent, row_idx, text):
    tk.Label(parent, text=text, font=FONT_TTL,
             bg=BG2, fg=ACCENT2, anchor="w"
             ).grid(row=row_idx, column=0, columnspan=3,
                    sticky="w", padx=8, pady=(6, 2))

# ── FixedBox : boîte à taille fixe (entrée ou sortie) ─────────────────────
class FixedBox:
    def __init__(self, parent, top_lbl, hint, is_output=False):
        self.is_output = is_output
        self.root = None   # injecté après placement

        self.frame = tk.Frame(parent, bg=BG3,
                              width=BOX_W, height=BOX_H,
                              highlightthickness=1,
                              highlightbackground=BOX_HL)
        self.frame.grid_propagate(False)   # taille imposée

        self.frame.rowconfigure(0, weight=0)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=0)
        self.frame.columnconfigure(0, weight=1)

        tk.Label(self.frame, text=top_lbl, bg=BG3, fg=FG2,
                 font=FONT_HINT, anchor="w"
                 ).grid(row=0, column=0, sticky="w", padx=6, pady=(3, 0))

        if is_output:
            self.widget = tk.Label(self.frame, text="", font=FONT_RES,
                                   bg=BG3, fg=OK_COL, anchor="w",
                                   justify="left", wraplength=BOX_W - 14)
        else:
            self.widget = tk.Entry(self.frame, font=FONT_MONO,
                                   bg=BG3, fg=FG, insertbackground=FG,
                                   relief="flat", bd=2,
                                   highlightthickness=0)
        self.widget.grid(row=1, column=0, sticky="ew", padx=6)

        tk.Label(self.frame, text=hint, bg=BG3, fg=FG2,
                 font=FONT_HINT, anchor="w"
                 ).grid(row=2, column=0, sticky="w", padx=6, pady=(0, 3))

    def get(self):
        return self.widget.get().strip() if not self.is_output else ""

    def show(self, text, ok=True):
        self.widget.config(text=text, fg=OK_COL if ok else ERR_COL)
        if ok and self.root:
            copy_clip(self.root, text)

    def insert(self, text):
        if not self.is_output:
            self.widget.delete(0, "end")
            self.widget.insert(0, text)

    def bind_enter(self, cmd):
        if not self.is_output:
            self.widget.bind("<Return>", lambda _: cmd())


# ── GridLayout : conteneur principal d'un onglet ──────────────────────────
class GridLayout(tk.Frame):
    """
    Frame principale d'un onglet.
    Colonnes :  0=entrée  1=bouton  2=sortie
    Chaque ConvertRow occupe une ligne grid.
    """
    def __init__(self, parent):
        super().__init__(parent, bg=BG2)
        self.pack(fill="both", expand=True, padx=10, pady=6)

        # Colonnes : entrée et sortie même poids, bouton fixe au centre
        self.columnconfigure(0, weight=0, minsize=BOX_W)
        self.columnconfigure(1, weight=0, minsize=BTN_W)
        self.columnconfigure(2, weight=0, minsize=BOX_W)

        # Centrage horizontal du bloc 3 colonnes
        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="both", expand=True)
        # On replace self dans outer centré
        self.pack_forget()
        self.master = outer
        outer_inner = tk.Frame(outer, bg=BG2)
        outer_inner.pack(anchor="center", pady=6)

        self._grid = outer_inner
        self._grid.columnconfigure(0, weight=0, minsize=BOX_W)
        self._grid.columnconfigure(1, weight=0, minsize=BTN_W)
        self._grid.columnconfigure(2, weight=0, minsize=BOX_W)

        self._next_row = 0

    def add_title(self, text):
        r = self._next_row
        tk.Label(self._grid, text=text, font=FONT_TTL,
                 bg=BG, fg=ACCENT2, anchor="w"
                 ).grid(row=r, column=0, columnspan=3,
                        sticky="w", padx=4, pady=(8, 2))
        self._next_row += 1

    def add_separator(self):
        r = self._next_row
        tk.Frame(self._grid, bg=SEP, height=1
                 ).grid(row=r, column=0, columnspan=3,
                        sticky="ew", padx=4, pady=4)
        self._next_row += 1

    def add_row(self, inbox: FixedBox, btn_text, callback, outbox: FixedBox):
        """Place une ligne  [inbox | bouton | outbox]  dans la grille."""
        r = self._next_row
        root = self._grid.winfo_toplevel()
        inbox.root  = root
        outbox.root = root

        inbox.bind_enter(callback)

        inbox.frame.grid(row=r, column=0, padx=(4, COL_PAD), pady=3, sticky="nsew")

        btn = tk.Button(self._grid, text=btn_text, command=callback,
                        font=FONT_BTN,
                        bg=ACCENT, fg="white",
                        activebackground=ACCENT2, activeforeground="white",
                        relief="flat", bd=0, cursor="hand2",
                        width=8)
        btn.grid(row=r, column=1, padx=4, pady=3, sticky="ns")

        outbox.frame.grid(row=r, column=2, padx=(COL_PAD, 4), pady=3, sticky="nsew")

        self._next_row += 1

    def add_raw_row(self, widget, colspan=3):
        """Ajoute un widget arbitraire sur toute la largeur."""
        r = self._next_row
        widget.grid(row=r, column=0, columnspan=colspan,
                    sticky="ew", padx=4, pady=2)
        self._next_row += 1

    @property
    def grid_frame(self):
        return self._grid


# ══════════════════════════════════════════════════════════════════════════
# Onglet RA / DEC
# ══════════════════════════════════════════════════════════════════════════
class RADecTab:
    def __init__(self, parent, root):
        self.root = root
        g = GridLayout(parent)
        f = g.grid_frame          # raccourci

        # ── Section 1 : Sexagésimal → Décimal ─────────────────────────
        g.add_title("Sexagésimal  →  Décimal")

        self.in_ra_s   = FixedBox(f, "RA  (hh mm ss.s)",
                                  "ex : 05 34 32.0 ou 05h34m32s ou 05:34:32")
        self.out_ra_s  = FixedBox(f, "RA décimal", "heures décimaux",
                                  is_output=True)
        g.add_row(self.in_ra_s,  "→ déc.", self._conv_ra_s2d,  self.out_ra_s)

        self.in_dec_s  = FixedBox(f, "DEC  (±dd mm ss.s)",
                                  "ex : +22 00 52.0 ou -05d12m33s ou -05:12:33")
        self.out_dec_s = FixedBox(f, "DEC décimal", "degrés décimaux",
                                  is_output=True)
        g.add_row(self.in_dec_s, "→ déc.", self._conv_dec_s2d, self.out_dec_s)

        g.add_separator()

        # ── Section 2 : Décimal → Sexagésimal ─────────────────────────
        g.add_title("Décimal  →  Sexagésimal")

        self.in_ra_d   = FixedBox(f, "RA  (heures décimaux)",
                                  "ex : 5.575556   plage [0 à 24]")
        self.out_ra_d  = FixedBox(f, "RA sexagésimal", "hh mm ss.sss",
                                  is_output=True)
        g.add_row(self.in_ra_d,  "→ sex.", self._conv_ra_d2s,  self.out_ra_d)

        self.in_dec_d  = FixedBox(f, "DEC  (degrés décimaux)",
                                  "ex : +22.014444   plage [-90 à +90]")
        self.out_dec_d = FixedBox(f, "DEC sexagésimal", "±dd mm ss.sss",
                                  is_output=True)
        g.add_row(self.in_dec_d, "→ sex.", self._conv_dec_d2s, self.out_dec_d)

    # ── Conversions ────────────────────────────────────────────────────
    def _conv_ra_s2d(self):
        raw = self.in_ra_s.get()
        if not raw:
            self.out_ra_s.show("⚠ Entrez une valeur RA", ok=False); return
        try:
            mo = re.match(r'(\d+)[hH:\s]\s*(\d+)[mM:\s]\s*([\d.]+)', raw)
            if mo:
                errs = validate_sexagesimal(int(mo.group(1)), int(mo.group(2)),
                                            float(mo.group(3)), "RA")
                if errs: self.out_ra_s.show("⚠ " + "  ".join(errs), ok=False); return
            v = parse_ra(raw)
            self.out_ra_s.show(f"{v:.6f} h")
        except ValueError as e:
            self.out_ra_s.show(f"⚠ {e}", ok=False)

    def _conv_dec_s2d(self):
        raw = self.in_dec_s.get()
        if not raw:
            self.out_dec_s.show("⚠ Entrez une valeur DEC", ok=False); return
        try:
            sign = "-" if raw.startswith("-") else "+"
            mo = re.match(r'(\d+)[dD:°\s]\s*(\d+)[mM\':\s]\s*([\d.]+)',
                          raw.lstrip("+-"))
            if mo:
                errs = validate_sexagesimal(int(mo.group(1)), int(mo.group(2)),
                                            float(mo.group(3)), "DEC")
                if errs: self.out_dec_s.show("⚠ " + "  ".join(errs), ok=False); return
            v = parse_dec(raw)
            self.out_dec_s.show(f"{v:+.6f}°")
        except ValueError as e:
            self.out_dec_s.show(f"⚠ {e}", ok=False)

    def _conv_ra_d2s(self):
        raw = self.in_ra_d.get()
        if not raw:
            self.out_ra_d.show("⚠ Entrez une valeur RA", ok=False); return
        try:
            v = float(raw)
            errs = validate_decimal_ra(v)
            if errs: self.out_ra_d.show("⚠ " + "  ".join(errs), ok=False); return
            h, m, s = ra_dec2sex(v)
            self.out_ra_d.show(fmt_ra_sex(h, m, s))
        except ValueError:
            self.out_ra_d.show("⚠ Valeur numérique attendue", ok=False)

    def _conv_dec_d2s(self):
        raw = self.in_dec_d.get()
        if not raw:
            self.out_dec_d.show("⚠ Entrez une valeur DEC", ok=False); return
        try:
            v = float(raw)
            errs = validate_decimal_dec(v)
            if errs: self.out_dec_d.show("⚠ " + "  ".join(errs), ok=False); return
            sg, d, m, s = dec_dec2sex(v)
            self.out_dec_d.show(fmt_dec_sex(sg, d, m, s))
        except ValueError:
            self.out_dec_d.show("⚠ Valeur numérique attendue", ok=False)


# ══════════════════════════════════════════════════════════════════════════
# Onglet Période
# ══════════════════════════════════════════════════════════════════════════
class PeriodTab:
    def __init__(self, parent, root):
        self.root = root
        g = GridLayout(parent)
        f = g.grid_frame

        # ── Section 1 : Jours → hms ───────────────────────────────────
        g.add_title("Jours décimaux  →  jj  hh  mm  ss")

        self.in_j2h  = FixedBox(f, "Période (jours décimaux)",
                                 "ex : 0.33695 (RR Lyr)   1.08857 (δ Cep)")
        self.out_j2h = FixedBox(f, "Période hms", "jj hh mm ss.sss",
                                 is_output=True)
        g.add_row(self.in_j2h, "→ hms", self._day2hms, self.out_j2h)

        g.add_separator()

        # ── Section 2a : 4 champs → Jours ────────────────────────────
        g.add_title("jj  hh  mm  ss  →  Jours décimaux")

        # Boîte d'entrée groupée (4 champs, taille BOX_W × BOX_H fixe)
        self.in_hms4 = tk.Frame(f, bg=BG3, width=BOX_W, height=BOX_H,
                                 highlightthickness=1, highlightbackground=BOX_HL)
        self.in_hms4.grid_propagate(False)
        self.in_hms4.columnconfigure(0, weight=1)
        self.in_hms4.rowconfigure(0, weight=0)
        self.in_hms4.rowconfigure(1, weight=1)
        self.in_hms4.rowconfigure(2, weight=0)

        tk.Label(self.in_hms4, text="jj  hh  mm  ss", bg=BG3, fg=FG2,
                 font=FONT_HINT, anchor="w"
                 ).grid(row=0, column=0, sticky="w", padx=6, pady=(3,0))

        sub = tk.Frame(self.in_hms4, bg=BG3)
        sub.grid(row=1, column=0, sticky="w", padx=4)

        for lbl_t, attr, w, ph in [
            ("j","e_d",3,"0"), ("h","e_h",3,"8"),
            ("min","e_m",3,"3"), ("s","e_s",6,"42.08")
        ]:
            tk.Label(sub, text=lbl_t, bg=BG3, fg=FG2,
                     font=FONT_HINT).pack(side="left", padx=(6,1))
            e = tk.Entry(sub, width=w, font=FONT_MONO,
                         bg=BG3, fg=FG, insertbackground=FG,
                         relief="flat", bd=2, highlightthickness=0)
            e.insert(0, ph)
            e.pack(side="left", padx=(0,2))
            setattr(self, attr, e)
            e.bind("<Return>", lambda _: self._hms2day_fields())

        tk.Label(self.in_hms4, text="ex : 0  8  3  42.08",
                 bg=BG3, fg=FG2, font=FONT_HINT, anchor="w"
                 ).grid(row=2, column=0, sticky="w", padx=6, pady=(0,3))

        self.out_hms4 = FixedBox(f, "Période décimale", "jours décimaux",
                                  is_output=True)
        self.out_hms4.root = root

        # Placement manuel dans la grille pour cette ligne spéciale
        r = g._next_row
        self.in_hms4.grid(row=r, column=0, padx=(4, COL_PAD), pady=3, sticky="nsew")
        btn4 = tk.Button(f, text="→ jours", command=self._hms2day_fields,
                         font=FONT_BTN, bg=ACCENT, fg="white",
                         activebackground=ACCENT2, activeforeground="white",
                         relief="flat", bd=0, cursor="hand2", width=8)
        btn4.grid(row=r, column=1, padx=4, pady=3, sticky="ns")
        self.out_hms4.frame.grid(row=r, column=2, padx=(COL_PAD, 4), pady=3, sticky="nsew")
        g._next_row += 1


    # ── Conversions ────────────────────────────────────────────────────
    def _day2hms(self):
        raw = self.in_j2h.get()
        if not raw:
            self.out_j2h.show("⚠ Entrez une période en jours", ok=False); return
        try:
            p = parse_period(raw)
            errs = validate_period(p)
            if errs: self.out_j2h.show("⚠ " + "  ".join(errs), ok=False); return
            d, h, m, s = period_day2hms(p)
            self.out_j2h.show(fmt_period_hms(d, h, m, s))
        except ValueError as e:
            self.out_j2h.show(f"⚠ {e}", ok=False)

    def _hms2day_fields(self):
        try:
            d = int(self.e_d.get() or 0)
            h = int(self.e_h.get() or 0)
            m = int(self.e_m.get() or 0)
            s = float(self.e_s.get() or 0)
            errs = []
            if not (0 <= h < 24): errs.append(f"Heures {h} invalides [0–23]")
            if not (0 <= m < 60): errs.append(f"Minutes {m} invalides [0–59]")
            if not (0 <= s < 60): errs.append(f"Secondes {s:.3f} invalides")
            if errs: self.out_hms4.show("⚠ " + "  ".join(errs), ok=False); return
            self.out_hms4.show(fmt_period_day(period_hms2day(d, h, m, s)))
        except ValueError as e:
            self.out_hms4.show(f"⚠ {e}", ok=False)


# ══════════════════════════════════════════════════════════════════════════
# Application
# ══════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Convertisseur Sex Dec de Martine")
        self.configure(bg=BG)
        self.resizable(True, False)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=FG2,
                        font=("Segoe UI", 9, "bold"), padding=[18, 5])
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT3)],
                  foreground=[("selected", "#ffffff")])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, pady=4)

        tab_rd = tk.Frame(nb, bg=BG, pady=4)
        tab_p  = tk.Frame(nb, bg=BG, pady=4)
        nb.add(tab_rd, text="  RA / DEC  ")
        nb.add(tab_p,  text="  Période   ")

        RADecTab(tab_rd, self)
        PeriodTab(tab_p,  self)

        ftr = tk.Frame(self, bg=SEP, pady=3)
        ftr.pack(fill="x")
        tk.Label(ftr,
                 text="Résultat copié dans le presse-papiers  —  Entrée pour valider",
                 font=FONT_HINT, bg=SEP, fg=FG2).pack()

        self.after(60, self._size)

    def _size(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


if __name__ == "__main__":
    App().mainloop()
