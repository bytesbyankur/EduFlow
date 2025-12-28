import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="omop@1280",
        database="attendance_db",
        autocommit=False
    )
