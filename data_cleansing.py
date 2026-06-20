import pandas as pd
import numpy as np
import os

# read csv file
data = pd.read_csv(r"iot_telemetry_data cleaning.csv", index_col=False)   # update file path to match csv file to be loaded

# only keep relevant columns
data = data[['device', 'co', 'humidity', 'lpg', 'smoke', 'temp']]

# set start and end date
start_date = "2025-09-01T00:00:00"
end_date = "2025-10-31T23:59:59"

# convert to datetime and specify number of timestamps
start = pd.to_datetime(start_date)
end = pd.to_datetime(end_date)
n = 405184

# create random timestamps
random_timestamps = start + (end - start) * np.random.rand(n)

# put timestamps into a dataframe, convert to datetime, sort in ascending order
df = pd.DataFrame({'ts': random_timestamps})
df['ts'] = pd.to_datetime(df['ts'])
df = df.sort_values(by='ts').reset_index(drop=True)
df["ts"] = df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")

# join the two dataframes so that each entry has a timestamp
new_data = df.join(data)

# rename columns
new_data.rename(columns={'ts': 'TimeStamp', 'device': 'DeviceName', 'co': 'CarbonMonoxide', 'humidity': 'Humidity',
                         'lpg': 'LPG', 'smoke': 'Smoke', 'temp': 'Temperature'}, inplace=True)

# file path
file_path = os.path.join(os.getcwd(), "telemetry_data.csv")

# save data without index, returns error if not successful
try:
    new_data.to_csv(file_path, index=False, encoding="utf-8")
    print(f"Data successfully saved to {file_path}")

except OSError as e:
    print(f"Error saving file: {e}")
