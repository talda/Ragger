import argparse
import os

from Ragger.index import Index


def main(data_folder, index_name):
    # Your logic here
    print(f"Folder: {data_folder}")
    print(f"Index: {index_name}")

    # Example: Check if the folder exists
    if os.path.isdir(data_folder):
        print(f"The folder '{data_folder}' exists.")
    else:
        print(f"The folder '{data_folder}' does not exist.")

    index_instance = Index(index_name)

    index_instance.process_text_files(data_folder)


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Process a folder and an index.")

    # Add arguments
    parser.add_argument("--folder_name", type=str, help="The name of the folder")
    parser.add_argument("--index_name", type=str, help="The name of the index")

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function
    main(args.folder_name, args.index_name)
