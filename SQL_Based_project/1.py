import mysql.connector

cnx = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    passwd="password123",
    database="testdb",
    port=3306
)
cnx.close()