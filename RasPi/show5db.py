#!/bin/python3
import sqlite3

DB_FILE = "bme280_data.db"

def show_last_records(n=5):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM bme280_data
        ORDER BY device_ts DESC
        LIMIT ?
    """, (n,))
    rows = cursor.fetchall()

    # Extract column names
    col_names = [description[0] for description in cursor.description]
    conn.close()

    # Print header
    print(f"Last {n} records in {DB_FILE}:")
    print("-" * 70)
    print(" | ".join(f"{name:>12}" for name in col_names))
    print("-" * 70)

    # Print rows
    for r in rows:
        print(" | ".join(f"{v:>12}" for v in r))

if __name__ == "__main__":
    show_last_records()
