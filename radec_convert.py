#!/usr/bin/env python3
"""
Conversion coordonnées RA/DEC : sexagésimal <-> décimal
Conversion période : jours décimaux <-> hh mm ss
"""

import re
import sys


# ── Sexagésimal → Décimal ──────────────────────────────────────────────────

def ra_sex2dec(h, m, s):
    """RA sexagésimal (hh mm ss) -> décimal (heures)."""
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"RA invalide : {h}h {m}m {s}s")
    return h + m / 60 + s / 3600


def dec_sex2dec(d, m, s, sign="+"):
    """DEC sexagésimal (±dd mm ss) -> décimal (degrés)."""
    if not (0 <= abs(d) <= 90 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"DEC invalide : {sign}{d} {m} {s}")
    value = abs(d) + m / 60 + s / 3600
    return -value if (sign == "-" or d < 0) else value


# ── Décimal → Sexagésimal ──────────────────────────────────────────────────

def ra_dec2sex(ra_h):
    """RA décimal (heures) -> (h, m, s)."""
    if not (0 <= ra_h < 24):
        raise ValueError(f"RA invalide : {ra_h} h")
    h = int(ra_h)
    rem = (ra_h - h) * 60
    m = int(rem)
    s = (rem - m) * 60
    return h, m, s


def dec_dec2sex(dec_deg):
    """DEC décimal (degrés) -> (signe, d, m, s)."""
    if not (-90 <= dec_deg <= 90):
        raise ValueError(f"DEC invalide : {dec_deg}")
    sign = "-" if dec_deg < 0 else "+"
    val = abs(dec_deg)
    d = int(val)
    rem = (val - d) * 60
    m = int(rem)
    s = (rem - m) * 60
    return sign, d, m, s


# ── Conversion période ─────────────────────────────────────────────────────

def period_day2hms(days):
    """Période en jours décimaux -> (jours entiers, h, m, s)."""
    if days < 0:
        raise ValueError(f"Période invalide : {days} j (doit être >= 0)")
    d = int(days)
    rem_h = (days - d) * 24
    h = int(rem_h)
    rem_m = (rem_h - h) * 60
    m = int(rem_m)
    s = (rem_m - m) * 60
    return d, h, m, s


def period_hms2day(d, h, m, s):
    """Période (jours entiers, hh, mm, ss.sss) -> jours décimaux."""
    if d < 0 or not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"Période invalide : {d}j {h}h {m}m {s}s")
    return d + h / 24 + m / 1440 + s / 86400


# ── Formatage ──────────────────────────────────────────────────────────────

def fmt_ra_sex(h, m, s):
    return f"{h:02d}h {m:02d}m {s:06.3f}s"

def fmt_dec_sex(sign, d, m, s):
    return f"{sign}{d:02d} {m:02d}' {s:06.3f}\""

def fmt_ra_dec(ra_h):
    return f"{ra_h:.6f} h"

def fmt_dec_dec(dec_deg):
    return f"{dec_deg:+.6f}"

def fmt_period_hms(d, h, m, s):
    if d:
        return f"{d}j {h:02d}h {m:02d}m {s:06.3f}s"
    return f"{h:02d}h {m:02d}m {s:06.3f}s"

def fmt_period_day(days):
    return f"{days:.8f} j"


# ── Parseurs ───────────────────────────────────────────────────────────────

def parse_ra(txt):
    """
    Accepte :
      '12 34 56.78'   '12h34m56.78s'   '12:34:56.78'   '12.5678'
    Retourne ra_h (float) en heures.
    """
    txt = txt.strip()
    if re.fullmatch(r'[\d.]+', txt):
        return float(txt)
    mo = re.match(r'(\d+)[hH:\s]\s*(\d+)[mM:\s]\s*([\d.]+)', txt)
    if mo:
        return ra_sex2dec(int(mo.group(1)), int(mo.group(2)), float(mo.group(3)))
    raise ValueError(f"Format RA non reconnu : '{txt}'")


def parse_dec(txt):
    """
    Accepte :
      '+42 30 00'   '-05d12m33.5s'   '+42:30:00'   '+42.5'   '42.5'
    Retourne dec_deg (float) en degrés.
    """
    txt = txt.strip()
    sign_char = "-" if txt.startswith("-") else "+"
    s_clean = txt.lstrip("+-")
    if re.fullmatch(r'[\d.]+', s_clean):
        v = float(s_clean)
        return -v if sign_char == "-" else v
    mo = re.match(r'(\d+)[dD:°\s]\s*(\d+)[mM\':\s]\s*([\d.]+)', s_clean)
    if mo:
        return dec_sex2dec(int(mo.group(1)), int(mo.group(2)),
                           float(mo.group(3)), sign_char)
    raise ValueError(f"Format DEC non reconnu : '{txt}'")


def parse_period(txt):
    """
    Accepte :
      '1.23456'            jours décimaux
      '1j 05h 37m 46.2s'   jours + hms
      '05h 37m 46.2s'      hms sans jours
      '1 05 37 46.2'       jours h m s séparés par espaces
      '05 37 46.2'         h m s séparés
    Retourne des jours décimaux (float).
    """
    txt = txt.strip()
    # décimal pur
    if re.fullmatch(r'[\d.]+', txt):
        return float(txt)
    # jours + hms  : 1j 05h 37m 46.2s  (ou 1d ...)
    mo = re.match(
        r'(\d+)\s*[jJdD]\s*(\d+)\s*[hH]\s*(\d+)\s*[mM\']\s*([\d.]+)\s*[sS]?',
        txt)
    if mo:
        return period_hms2day(int(mo.group(1)), int(mo.group(2)),
                              int(mo.group(3)), float(mo.group(4)))
    # hms seuls : 05h 37m 46.2s
    mo = re.match(r'(\d+)\s*[hH]\s*(\d+)\s*[mM\']\s*([\d.]+)\s*[sS]?', txt)
    if mo:
        return period_hms2day(0, int(mo.group(1)),
                              int(mo.group(2)), float(mo.group(3)))
    # 4 champs numériques : jours h m s
    mo = re.match(r'(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)', txt)
    if mo:
        return period_hms2day(int(mo.group(1)), int(mo.group(2)),
                              int(mo.group(3)), float(mo.group(4)))
    # 3 champs numériques : h m s
    mo = re.match(r'(\d+)\s+(\d+)\s+([\d.]+)', txt)
    if mo:
        return period_hms2day(0, int(mo.group(1)),
                              int(mo.group(2)), float(mo.group(3)))
    raise ValueError(f"Format de période non reconnu : '{txt}'")


# ── Démo ───────────────────────────────────────────────────────────────────

def demo():
    print("=" * 57)
    print("  Convertisseur RA/DEC  sexagésimal <-> décimal")
    print("  Convertisseur Période jours <-> hh mm ss")
    print("=" * 57)

    exemples = [
        ("05 34 32.0", "+22 00 52.0"),   # M1 Crabe
        ("10 44 57.8", "+12 21 54.0"),   # M95
        ("23 23 26.0", "-20 50 30.0"),   # NGC 7619
    ]

    print("\n-- Sexagesimal -> Decimal ----------------------------------")
    for ra_s, dec_s in exemples:
        ra_h  = parse_ra(ra_s)
        dec_d = parse_dec(dec_s)
        print(f"  RA  {ra_s:>15s}  ->  {fmt_ra_dec(ra_h)}")
        print(f"  DEC {dec_s:>15s}  ->  {fmt_dec_dec(dec_d)}")
        print()

    print("-- Decimal -> Sexagesimal ----------------------------------")
    valeurs = [(5.5756, 22.0144), (10.7494, 12.3650), (23.3906, -20.8417)]
    for ra_h, dec_d in valeurs:
        h, m, s        = ra_dec2sex(ra_h)
        sg, d, dm, ds  = dec_dec2sex(dec_d)
        print(f"  RA  {ra_h:>10.4f} h  ->  {fmt_ra_sex(h, m, s)}")
        print(f"  DEC {dec_d:>+10.4f}    ->  {fmt_dec_sex(sg, d, dm, ds)}")
        print()

    print("-- Periode : jours decimaux -> hh mm ss --------------------")
    periodes_j = [
        (0.33695,  "RR Lyr"),
        (1.08857,  "delta Cep"),
        (5.36634,  "eta Aql"),
        (0.01042,  "~15 min  (transit court)"),
        (365.25,   "1 an"),
    ]
    for p, label in periodes_j:
        d, h, m, s = period_day2hms(p)
        print(f"  {p:>10.5f} j  ({label})")
        print(f"    -> {fmt_period_hms(d, h, m, s)}")
    print()

    print("-- Periode : hh mm ss -> jours decimaux --------------------")
    periodes_hms = [
        (0,   8,  3, 42.08, "RR Lyr"),
        (1,   2,  7, 33.65, "delta Cep"),
        (5,   8, 47, 40.18, "eta Aql"),
        (365, 6,  0,  0.0,  "1 an"),
    ]
    for d, h, m, s, label in periodes_hms:
        p = period_hms2day(d, h, m, s)
        print(f"  {fmt_period_hms(d, h, m, s):>30s}  ({label})")
        print(f"    -> {fmt_period_day(p)}")
    print()


# ── Mode interactif ────────────────────────────────────────────────────────

def interactive():
    print("\n-- Mode interactif (Ctrl-C pour quitter) -------------------")
    while True:
        try:
            print("\n  [1] RA/DEC : Sexagesimal  -> Decimal")
            print("  [2] RA/DEC : Decimal      -> Sexagesimal")
            print("  [3] Periode : jours dec   -> hh mm ss")
            print("  [4] Periode : hh mm ss   -> jours dec")
            choix = input("  Choix : ").strip()

            if choix == "1":
                ra_s  = input("  RA  (ex: 05 34 32.0  ou  05h34m32s) : ")
                dec_s = input("  DEC (ex: +22 00 52   ou  +22d00m52s) : ")
                ra_h  = parse_ra(ra_s)
                dec_d = parse_dec(dec_s)
                print(f"  -> RA  = {fmt_ra_dec(ra_h)}")
                print(f"  -> DEC = {fmt_dec_dec(dec_d)}")

            elif choix == "2":
                ra_h  = float(input("  RA  (heures decimaux, ex: 5.5756)  : "))
                dec_d = float(input("  DEC (degres decimaux, ex: +22.014) : "))
                h, m, s       = ra_dec2sex(ra_h)
                sg, d, dm, ds = dec_dec2sex(dec_d)
                print(f"  -> RA  = {fmt_ra_sex(h, m, s)}")
                print(f"  -> DEC = {fmt_dec_sex(sg, d, dm, ds)}")

            elif choix == "3":
                p_s = input("  Periode en jours (ex: 0.33695  ou  1.08857) : ")
                p = parse_period(p_s)
                d, h, m, s = period_day2hms(p)
                print(f"  -> {fmt_period_hms(d, h, m, s)}")

            elif choix == "4":
                p_s = input(
                    "  Periode (ex: '1j 02h 07m 33.6s'  "
                    "ou  '1 2 7 33.6'  ou  '08h 03m 42s') : ")
                p = parse_period(p_s)
                print(f"  -> {fmt_period_day(p)}")

            else:
                print("  Entrez 1, 2, 3 ou 4.")

        except ValueError as e:
            print(f"  Erreur : {e}")
        except KeyboardInterrupt:
            print("\n  Au revoir !")
            break


if __name__ == "__main__":
    demo()
    if "--interactive" in sys.argv or "-i" in sys.argv:
        interactive()
    else:
        print("  (Lancez avec -i pour le mode interactif)\n")
