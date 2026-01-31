import csv
import os


def get_data(file_name):
    """
    Extracts file from data folder for processing. Ensures compatibility across
    platforms.

    Arguments:
        file_name (String): The full file name of the file to be processed.

    Returns:
        String: The platform-specific path to the file.
    """
    folder_name = os.path.abspath(os.path.join("..", "data"))
    return os.path.join(folder_name, file_name)


def main():
    file_path = get_data("muse2_eeg_data.csv")

    # check file existence
    if not os.path.exists(file_path):
        print(f"file does not exist at: {file_path}")
        return

    with open(file_path, newline="") as csvfile:
        line = csv.reader(csvfile, delimiter=" ")

        for row in line:
            print(", ".join(row))


if __name__ == "__main__":
    main()
