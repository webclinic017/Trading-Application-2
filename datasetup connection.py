from mysql import connector
# import mysql-connector-python
import mysql.connector as my


mydb = my.connect(
    host="localhost",
    user="root",
    passwd="password123", auth_plugin='mysql_native_password')

print(mydb)
