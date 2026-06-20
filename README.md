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
