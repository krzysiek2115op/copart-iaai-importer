#!/usr/bin/env python3
"""
Seed przykładowych aut COPART do bazy — dla SYMULACJI VPS w GitHub Actions.

Copart live wymaga konta Member (anty-bot Incapsula), więc w CI nie zbierzemy go
realnie. Dokładamy więc kilka realistycznych aut Copart obok REALNYCH aut IAAI
z pipeline'u — żeby pokazać drugie źródło (plakietka/filtr). Idempotentne (ON DUPLICATE KEY UPDATE).

Env (te same co pipeline): IAAI_DB_HOST/PORT/NAME/USER/PASS, IAAI_DB_TABLE_PREFIX.
Uruchom:  python scraper/tools/seed_copart_demo.py
"""
import os
import sys

try:
    import pymysql
except ImportError:
    print("[seed_copart_demo] brak pymysql — pomijam (na VPS/CI będzie zainstalowany)")
    sys.exit(0)

PFX = os.environ.get("IAAI_DB_TABLE_PREFIX", "")
VEH = PFX + "iaai_vehicles"
IMG = PFX + "iaai_vehicle_images"

CARS = [
    dict(salvage_id=800001, source="copart", vin="1C4RJFAG5FC601234", year=2018, make="Jeep",
         model="Grand Cherokee", body_style="SUV", odometer=61240, odometer_uom="mi",
         primary_damage="Front End", color="Black", fuel_type="Gasoline", transmission="Automatic",
         drive_line="4WD", key_available="Yes", run_and_drive="Run and Drive", title="Salvage",
         selling_branch="TX - Dallas (Copart)", buy_now=12800, current_bid=8600,
         detail_url="https://www.copart.com/lot/800001", status="active"),
    dict(salvage_id=800002, source="copart", vin="5NPD84LF2JH123456", year=2018, make="Hyundai",
         model="Elantra", body_style="Sedan", odometer=44500, odometer_uom="mi",
         primary_damage="Rear End", color="White", fuel_type="Gasoline", transmission="Automatic",
         drive_line="FWD", key_available="Yes", run_and_drive="Run and Drive", title="Clean",
         selling_branch="CA - Los Angeles (Copart)", buy_now=7600, current_bid=5200,
         detail_url="https://www.copart.com/lot/800002", status="active"),
    dict(salvage_id=800003, source="copart", vin="1C6RR7GT6JS123456", year=2019, make="Ram",
         model="1500", body_style="Pickup", odometer=38700, odometer_uom="mi",
         primary_damage="Side", color="Silver", fuel_type="Gasoline", transmission="Automatic",
         drive_line="4WD", key_available="Yes", run_and_drive="Run and Drive", title="Salvage",
         selling_branch="FL - Miami (Copart)", buy_now=19900, current_bid=14500,
         detail_url="https://www.copart.com/lot/800003", status="active"),
]
IMGS = {
    800001: ["https://placehold.co/700x500/1e5fb0/ffffff?text=Jeep+Grand+Cherokee",
             "https://placehold.co/700x500/133b6e/ffffff?text=Grand+Cherokee+-+bok"],
    800002: ["https://placehold.co/700x500/1e5fb0/ffffff?text=Hyundai+Elantra"],
    800003: ["https://placehold.co/700x500/1e5fb0/ffffff?text=Ram+1500",
             "https://placehold.co/700x500/123a63/ffffff?text=Ram+1500+-+tyl"],
}


def main():
    conn = pymysql.connect(
        host=os.environ.get("IAAI_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("IAAI_DB_PORT", "3306")),
        user=os.environ.get("IAAI_DB_USER", "root"),
        password=os.environ.get("IAAI_DB_PASS", ""),
        database=os.environ.get("IAAI_DB_NAME", "iaai"),
        charset="utf8mb4",
    )
    cur = conn.cursor()
    for c in CARS:
        cols = list(c.keys())
        ph = ",".join(["%s"] * len(cols))
        upd = ",".join(f"`{k}`=VALUES(`{k}`)" for k in cols if k not in ("salvage_id", "source"))
        cur.execute(
            f"INSERT INTO {VEH} ({','.join('`'+k+'`' for k in cols)}) VALUES ({ph}) "
            f"ON DUPLICATE KEY UPDATE {upd}",
            [c[k] for k in cols],
        )
        for seq, url in enumerate(IMGS.get(c["salvage_id"], []), 1):
            cur.execute(
                f"INSERT INTO {IMG} (salvage_id,source,image_key,seq,width,height,url) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE url=VALUES(url),seq=VALUES(seq)",
                (c["salvage_id"], "copart", f"copart-{c['salvage_id']}-{seq}", seq, 700, 500, url),
            )
    conn.commit()
    cur.close()
    conn.close()
    print(f"[seed_copart_demo] wstawiono {len(CARS)} aut Copart (source=copart).")


if __name__ == "__main__":
    main()
