import mysql.connector
from mysql.connector import Error
from datetime import datetime
import uuid
import pandas as pd
import os
import time
import sys
import logging


# function to check if value is a positive number
def is_positive_number(value):
    try:
        return float(value) > 0
    except (ValueError, TypeError):
        return False


# function to check if value is a number
def is_number(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


# restart configuration
MAX_RESTARTS = 5
LOG_FILE = "batch_insert.log"

# logging setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# function to restart logging count
def get_restart_count():
    try:
        return int(os.environ.get("RESTART_COUNT", "0"))
    except ValueError:
        return 0


# function to restart application in the event of a failure, up to the specified maximum restart amount
def restart_script(delay=3):
    restart_count = get_restart_count()

    if restart_count >= MAX_RESTARTS:
        logging.error(f"❌ Max restart attempts ({MAX_RESTARTS}) reached. Stopping. Please check user operating system"
                      f"and upload file for errors before trying again.")
        print(f"❌ Max restart attempts ({MAX_RESTARTS}) reached. Stopping. Please check user operating system"
              f"and upload file for errors before trying again.")
        sys.exit(1)

    restart_count += 1
    os.environ["RESTART_COUNT"] = str(restart_count)

    logging.warning(f"Restart attempt {restart_count}/{MAX_RESTARTS} in {delay} seconds...")
    print(f"🔄 Restart attempt {restart_count}/{MAX_RESTARTS} in {delay} seconds...")
    time.sleep(delay)

    os.execl(sys.executable, sys.executable, *sys.argv)


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


# function to upload data in batches of 2500, checks that data in rows are valid, skips invalid rows and returns
# the number of rows skipped. If there is an error it restarts, after 5 attempts stops running. Advises of time
# taken for the batch upload for system health monitoring
def upload_batch(data_rows, batch_size=2500):
    if not isinstance(data_rows, list) or not all(isinstance(row, tuple) for row in data_rows):
        raise ValueError("data_rows must be a list of tuples.")

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero.")

    total_rows = len(data_rows)
    if total_rows == 0:
        print("⚠ No rows to insert.")
        return 0.0

    connection = None
    cursor = None
    start_time = time.perf_counter()

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
        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            chunk = data_rows[start:end]

            # Filter out invalid rows
            valid_chunk = [
                row for row in chunk
                if is_positive_number(row[2])  # CarbonMonoxide
                   and is_positive_number(row[3])  # Humidity
                   and is_positive_number(row[4])  # LPG
                   and is_positive_number(row[5])  # Smoke
                   and is_number(row[6])  # Temperature (can be negative)
            ]

            skipped_count = len(chunk) - len(valid_chunk)
            if skipped_count > 0:
                print(f"⚠ Skipped {skipped_count} invalid rows in this batch.")

            if not valid_chunk:
                continue  # Skip DB insert if no valid rows

            batch_name = valid_chunk[0][0]

            insert_query = """
                    INSERT INTO telemetry_data 
                    (BatchName, TimeStamp, DeviceName, CarbonMonoxide, Humidity, LPG, Smoke, Temperature)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

            rows_with_batch = [
                (batch_name, row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                for row in valid_chunk
            ]

            cursor.executemany(insert_query, rows_with_batch)
            connection.commit()

            print(f"✅ Inserted {len(valid_chunk)} rows with batch name: {batch_name}")
            logging.info(f"Inserted {len(valid_chunk)} rows with batch name: {batch_name}")

    except Error as e:
        print(f"❌ Database Error: {e}")
        logging.error(f"Database Error: {e}")
        if connection.is_connected():
            connection.rollback()
        restart_script()  # Restart on DB error

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        logging.exception(f"Unexpected Error: {e}")
        restart_script()  # Restart on any other error

    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

    elapsed_time = time.perf_counter() - start_time
    print(f"⏱ Total execution time: {elapsed_time:.4f} seconds")
    logging.info(f"Total execution time: {elapsed_time:.4f} seconds")
    return elapsed_time


# runs application and insert data
if __name__ == "__main__":
    data_to_insert = pd.read_csv("telemetry_data.csv")

    data_tuples = [tuple(row) for row in data_to_insert.itertuples(index=False, name=None)]
    upload_batch(data_tuples, batch_size=2500)
    exec_time = upload_batch(data_tuples, batch_size=2500)
    print(f"Returned execution time: {exec_time:.4f} seconds")
