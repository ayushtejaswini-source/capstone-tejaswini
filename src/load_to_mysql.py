import argparse
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
APPT_COLS = [
    "appointment_id",
    "patient_id",
    "gender",
    "age",
    "scheduled_date",
    "appointment_date",
    "lead_days",
    "lead_quartile",
    "clinic",
    "city",
    "specialty",
    "sms_received",
    "insurance_covered",
    "previous_no_shows",
    "avg_temp_c",
    "no_show",
]


def prepare_rows():
    clinics = pd.read_csv(ROOT / "data" / "clinics.csv")
    appts = pd.read_csv(ROOT / "data" / "Appointments_clean.csv")[APPT_COLS]
    clinic_rows = [tuple(r) for r in clinics.astype(object).itertuples(index=False, name=None)]
    appt_rows = [tuple(r) for r in appts.astype(object).itertuples(index=False, name=None)]
    return clinic_rows, appt_rows


def run_schema(cursor):
    text = (ROOT / "sql" / "01_schema.sql").read_text()
    text = "\n".join(l for l in text.splitlines() if not l.strip().startswith("--"))
    for stmt in filter(None, (s.strip() for s in text.split(";"))):
        cursor.execute(stmt)


def load(conn):
    clinic_rows, appt_rows = prepare_rows()
    cur = conn.cursor()
    run_schema(cur)
    cur.execute("USE careclick")
    cur.executemany("INSERT INTO clinics (clinic_id, clinic_name, city, latitude, longitude) "
                    "VALUES (%s, %s, %s, %s, %s)", clinic_rows)
    placeholders = ", ".join(["%s"] * len(APPT_COLS))
    sql = f"INSERT INTO appointments ({', '.join(APPT_COLS)}) VALUES ({placeholders})"
    for i in range(0, len(appt_rows), 2000):
        cur.executemany(sql, appt_rows[i:i + 2000])
    conn.commit()
    cur.execute("SELECT COUNT(*), SUM(no_show) FROM appointments")
    return cur.fetchone()


def connect(database=None):
    import mysql.connector

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=database,
    )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.dry_run:
        c, a = prepare_rows()
        print(f"dry run OK: {len(c)} clinic rows, {len(a):,} appointment rows ready to insert")
    else:
        total, no_shows = load(connect())
        print(f"loaded {total:,} appointments ({int(no_shows):,} no-shows) into MySQL database 'careclick'")
