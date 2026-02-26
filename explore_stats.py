# explore_stats.py
import pandas as pd

from src import data_processing

# Example DataFrame
fake_data = pd.DataFrame(
    {
        "delta": [1, 2, 3],
        "theta": [2, 3, 4],
        "alpha": [3, 4, 5],
        "beta": [4, 5, 6],
    }
)

# Get statistics
stats = data_processing.get_stats(fake_data)

# Print the results
print("--- Measures of Central Tendency ---")
print("Mean:\n", stats["mean"])
print("Median:\n", stats["median"])
print("Mode:\n", stats["mode"])

print("\n--- Measures of Dispersion ---")
print("Range:\n", stats["range"])
print("Variance:\n", stats["variance"])
print("Standard Deviation:\n", stats["std_dev"])
print("Interquartile Range:\n", stats["iqr"])
