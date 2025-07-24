import sqlite3
from config import DB_PATH

def drop_film_text_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS film_text;")
    conn.commit()
    conn.close()
    print("Table 'film_text' dropped (if it existed).")

if __name__ == "__main__":
    drop_film_text_table()