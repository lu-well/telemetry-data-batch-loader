import mysql.connector
from mysql.connector import Error
from datetime import datetime
import uuid
import pandas as pd
import os
import time


# create database connection, allows multiple attempts in case MySQL connection needs more time
def get_db_connection(retries=10, delay=3):
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")
    port = os.getenv("MYSQL_PORT")

    print("\n=== MYSQL ENV VARS IN PYTHON CONTAINER ===")
    print("HOST =", host)
    print("USER =", user)
    print("PASSWORD =", password)
    print("DATABASE =", database)
    print("PORT =", port)
    print("==========================================\n")

    for attempt in range(1, retries + 1):
        try:
            print(f"Attempt {attempt}/{retries}: Connecting to {host}:{port} ...")

            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=int(port)
            )

            if conn.is_connected():
                print("✅ Connected to MySQL successfully!")
                return conn

        except Error as e:
            print(f"❌ Connection failed: {e}")
            time.sleep(delay)

    raise RuntimeError("❌ Could not connect to MySQL after multiple attempts.")


# function to upload data in batches of 2500
def upload_batch(data_rows, batch_size=2500):
    connection = None
    cursor = None

    # connect to MySQL, create table and insert data
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # create telemetry data table
        cursor.execute("CREATE TABLE IF NOT EXISTS telemetry_data ("
                       "ID INT AUTO_INCREMENT PRIMARY KEY,"
                       "BatchName varchar(100) NOT NULL,"
                       "Timestamp TIMESTAMP,"
                       "DeviceName varchar(255),"
                       "CarbonMonoxide DECIMAL(20, 10),"
                       "Humidity DECIMAL(20, 10),"
                       "LPG DECIMAL(20, 10),"
                       "Smoke DECIMAL(20, 10),"
                       "Temperature DECIMAL(20, 10)"
                       ");")

        # insert batches
        total_rows = len(data_rows)
        for start in range(0, total_rows, batch_size):
            end = start + batch_size
            chunk = data_rows[start:end]

            # create unique batch names
            batch_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

            insert_query = """
                    INSERT INTO telemetry_data (BatchName, TimeStamp, DeviceName, CarbonMonoxide, Humidity, LPG, Smoke, 
                    Temperature)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

            # add batch names to entries
            rows_with_batch = [(batch_name, row[0], row[1], row[2], row[3], row[4], row[5], row[6]) for row in chunk]

            # insert statement
            cursor.executemany(insert_query, rows_with_batch)

            # commit to database
            connection.commit()

            print(f"✅ Inserted {len(chunk)} rows with batch name: {batch_name}")

    except Error as e:

        print(f"❌ Error: {e}")

        if connection is not None and connection.is_connected():
            connection.rollback()

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


# run and insert data
if __name__ == "__main__":
    data_to_insert = pd.read_csv("telemetry_data.csv")

    data_tuples = [tuple(row) for row in data_to_insert.itertuples(index=False, name=None)]
    upload_batch(data_tuples, batch_size=2500)
