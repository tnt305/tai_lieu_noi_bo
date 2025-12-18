import os

TARGET_DIR = "./src/etl/dataset"
EXCEPT_FILES = {"__init__.py"}

def clean_dataset_dir(path: str):
    if not os.path.isdir(path):
        raise ValueError(f"Not a directory: {path}")

    for filename in os.listdir(path):
        if filename in EXCEPT_FILES:
            continue

        file_path = os.path.join(path, filename)

        # chỉ xoá file, không xoá folder
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted: {filename}")

if __name__ == "__main__":
    clean_dataset_dir(TARGET_DIR)
