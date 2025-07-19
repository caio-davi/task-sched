import argparse
import logging
import csv

def read_tasks(filepath):
    with open(filepath, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        logging.info("Tasks loaded")
        return list(reader)

def parse_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "file", 
        help="File containing the data to process")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)"
    )
    
    return parser.parse_args()
    
if __name__ == "__main__":
    args = parse_args()
    task = read_tasks(args.file)
    for task in task:
        print (task)