import sqlite3
import pandas as pd

# Koneksi ke database SQLite
conn = sqlite3.connect("db.sqlite3")

# Tabel-tabel yang ingin diekspor
tables = ["api_photogallery"]

for table in tables:
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    df.to_csv(f"{table}.csv", index=False)

conn.close()
