import csv
import os

# Path to the dummy CSV file
file_path = os.path.join("data", "muse2_eeg_data.csv")

# Check if the file exists
if not os.path.exists(file_path):
    print(f"{file_path} not found!")
else:
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            print(row)
