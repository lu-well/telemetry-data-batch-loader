# Telemetry Data Batch Uploader

This app automatically uploads data from various environmental sensors into a MySQL table and stores it in batches 
so that information can be easily searched for and retrieved by the municipality who own the data. The app has been 
containerised in Docker so that it can be run on different machines and systems. The data system was designed to be 
straightforward so that it can be easily adjusted in the future to incorporate new sensor information.

## Project Objectives

To create a scalable, reliable and simple data system which stores environmental metrics for 
future use in warning applications.

## Data

The data used for this project was sourced from Kaggle: [Environmental Sensor Telemetry Data](https://www.kaggle.com/datasets/garystafford/environmental-sensor-data-132k) 

## Usage

Clone the repository:
```bash
git clone https://github.com/lu-well/telemetry-data-batch-loader.git
cd telemetry-data-batch-loader
```

Build the Docker container to run the app:
```bash
docker-compose up --build
```

Open a MySQL connection with port 3307 to view the data batches

Password: Admin1234!

To upload new data, ensure that it is saved in a CSV file with the following columns:

| TimeStamp | DeviceName | CarbonMonoxide | Humidity | LPG | Smoke | Temp |
|-----------|------------|----------------|----------|-----|-------|------|

Descriptions of the columns, and formatting and logical requirements for the data are as follows:
'TimeStamp' is the timestamp in format DD/MM/YYYY HH:MM:SS and entries must be in chronological order
'DeviceName' is the device name
'CarbonMonoxide' is the carbon monoxide level in parts per million percentage and must be a positive number
'Humidity' is the humidity level percentage and must be a positive number between 0 and 100
'LPG' is the LPG gas level in parts per million percentage and must be a positive number
'Smoke' is the smoke level in parts per million percentage and must be a positive number
'Temperature' is the temperature in degrees Celsius and must be a number, which can be positive or negative

If any of the data points in a row are incorrectly formatted, the entry will be skipped. At the end of the upload, a count of how many rows were skipped is shown. 

Chronological order is essential for future analyses as batches are named with the timestamp of the first entry. This means that they can be easily grouped and SQL queries run to extract data from a particular day/week/month to facilitate the future applications with tracking environmental metrics.

Time taken to upload all batches is displayed once the process is successfully completed, so that the speed and efficiency of the system can be monitored.

If the batch upload is unsuccessful, the system will automatically restart and attempt to complete the task again, up to 5 times. If it is still unsuccessful after 5 attempts, an error message is returned advising the user to check for issues in the upload file and their operating system.
