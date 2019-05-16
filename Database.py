import sqlite3

conn = sqlite3.connect('database.db')

c = conn.cursor()

'''c.execute("""CREATE TABLE ohlc_one_min(
            Symbol text,
            Time text,
            Open real,
            High real,
            Low real,
            Close real,
            TR real,
            ATR real
            )""")
'''
conn.commit()

conn.close()
