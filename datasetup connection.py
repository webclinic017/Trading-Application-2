import mysql.connector as my


mydb = my.connect(
    host="localhost",
    user="root",
    passwd="password123",
    database="testdb")

print(mydb)

my_cursor = mydb.cursor()

# my_cursor.execute("CREATE DATABASE testdb")

# my_cursor.execute("CREATE TABLE users (name VARCHAR(255), email VARCHAR(255), age INTEGER(10), user_id INTEGER AUTO_INCREMENT PRIMARY KEY)")

first_user = "INSERT INTO users (name, email, age) values (%s, %s, %s)"
record1 = ("divya", "karanam", 20)

my_cursor.execute(first_user, record1)
mydb.commit()