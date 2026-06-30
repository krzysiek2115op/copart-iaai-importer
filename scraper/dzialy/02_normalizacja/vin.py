"""
Dział 2 · NORMALIZACJA — agent `VIN`  (+ krytyk `poprawność-VIN`).

- waliduje format VIN (17 znaków, dozwolone znaki, bez I/O/Q)
- liczy cyfrę kontrolną wg ISO 3779 / FMVSS 565 (tylko pełne VIN-y)
- wykrywa maskowanie (anonimowy IAAI maskuje numer seryjny: ...******)
- dekoduje przez NHTSA vPIC (działa też dla zamaskowanych) -> make/model/year/body
  i krzyżowo sprawdza z danymi ze scrapingu.

Referencja: docs/refs/vin-nhtsa.md
Wymagania: pip install requests
Użycie:   python vin.py --in out/szczegoly.jsonl --out out/norm_vin.jsonl
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

import requests

VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues"
ALLOWED = set("ABCDEFGHJKLMNPRSTUVWXYZ0123456789")          # bez I, O, Q
TRANSLIT = {**{c: i for i, c in enumerate("0123456789", 0)},
            "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
            "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
            "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9}
WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def clean_vin(vin: str) -> str:
    return re.sub(r"\s+", "", (vin or "")).upper()


def is_masked(vin: str) -> bool:
    return "*" in vin or "X" in vin[11:]      # IAAI maskuje gwiazdką (poz. 12-17)


def format_ok(vin: str) -> bool:
    return len(vin) == 17 and all(c in ALLOWED or c == "*" for c in vin)


def check_digit_ok(vin: str) -> bool | None:
    """True/False dla pełnych VIN; None gdy nie da się policzyć (maska/zły format)."""
    if len(vin) != 17 or any(c not in TRANSLIT for c in vin):
        return None
    total = sum(TRANSLIT[c] * w for c, w in zip(vin, WEIGHTS))
    expected = "X" if total % 11 == 10 else str(total % 11)
    return vin[8] == expected


def decode_vpic(vin: str, year=None, session: requests.Session = None) -> dict:
    s = session or requests
    params = {"format": "json"}
    if year:
        params["modelyear"] = year
    r = s.get(f"{VPIC}/{vin}", params=params, timeout=30)
    r.raise_for_status()
    res = r.json()["Results"][0]
    return {
        "make": (res.get("Make") or "").title() or None,
        "model": res.get("Model") or None,
        "year": int(res["ModelYear"]) if res.get("ModelYear", "").isdigit() else None,
        "body_class": res.get("BodyClass") or None,
        "fuel": res.get("FuelTypePrimary") or None,
        "cylinders": int(res["EngineCylinders"]) if (res.get("EngineCylinders") or "").isdigit() else None,
        "drive": res.get("DriveType") or None,
    }


def normalize(rec: dict, session: requests.Session) -> dict:
    vin = clean_vin(rec.get("vin", ""))
    out = dict(rec)
    out["vin"] = vin or None
    out["vin_masked"] = bool(vin) and is_masked(vin)
    out["vin_format_ok"] = format_ok(vin) if vin else False
    out["vin_check_digit_ok"] = check_digit_ok(vin) if vin else None
    # L10: vin_status spójny (gdy szczegóły nie podały go w nawiasie, wyprowadź z walidacji).
    if not out.get("vin_status"):
        if not vin:
            out["vin_status"] = None
        elif out["vin_masked"]:
            out["vin_status"] = "masked"
        elif out["vin_check_digit_ok"] is True:
            out["vin_status"] = "ok"
        elif out["vin_check_digit_ok"] is False:
            out["vin_status"] = "invalid"
        else:
            out["vin_status"] = "unknown"
    out["vpic"] = None
    if vin and out["vin_format_ok"]:
        try:
            dec = decode_vpic(vin, rec.get("year"), session)
            out["vpic"] = dec
            # krzyżowa kontrola / uzupełnienie braków
            for k in ("make", "model", "year"):
                if dec.get(k) and not out.get(k):
                    out[k] = dec[k]
            out["make_mismatch"] = bool(dec.get("make") and rec.get("make")
                                        and dec["make"].lower() != str(rec["make"]).lower())
        except Exception as e:
            out["vpic_error"] = str(e)[:120]
    return out


# ---- 🔴 KRYTYK: poprawność-VIN --------------------------------------------
def krytyk_poprawnosc_vin(rec: dict) -> list[str]:
    issues = []
    if not rec.get("vin"):
        issues.append("brak VIN")
        return issues
    if not rec.get("vin_format_ok"):
        issues.append("VIN nie ma poprawnego formatu (17 znaków / dozwolone znaki)")
    if rec.get("vin_check_digit_ok") is False:
        issues.append("cyfra kontrolna VIN niepoprawna")
    if rec.get("vin_masked"):
        issues.append("VIN zamaskowany (anonimowo) — pełna walidacja niemożliwa; make/model z vPIC")
    if rec.get("make_mismatch"):
        issues.append(f"marka ze scrapingu != vPIC ({rec.get('make')})")
    if rec.get("vpic_error"):
        issues.append("błąd dekodowania vPIC: " + rec["vpic_error"])
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("out/norm_vin.jsonl"))
    args = ap.parse_args()

    session = requests.Session()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rc = 0
    with args.out.open("w", encoding="utf-8") as fh:
        for line in args.infile.read_text().splitlines():
            if not line.strip():
                continue
            rec = normalize(json.loads(line), session)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            issues = krytyk_poprawnosc_vin(rec)
            v = rec.get("vpic") or {}
            status = "OK ✅" if not issues else "; ".join(issues)
            print(f"  {rec.get('salvage_id')}: VIN {rec.get('vin')} -> "
                  f"vPIC {v.get('make')} {v.get('model')} {v.get('year')} | [{status}]")
            if issues and not rec.get("vin_masked"):
                rc = 1
    print(f"[VIN] zapisano -> {args.out}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
