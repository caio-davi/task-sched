import argparse
import logging
import csv
import subprocess

TASKS_PATH="./tests/tasks/"

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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate the input task list and output the expected total runtime"
    )
    
    return parser.parse_args()

def read_tasks(filepath):
    with open(filepath, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        logging.info("Tasks loaded")
        return list(reader)

def run_cmd(command):
    try:
        subprocess.run([f"{TASKS_PATH}{command}"])
        logging.info(f"Task {command} executed succefully")
    except subprocess.CalledProcessError:
        logging.error(f"Task {command} failed")

def expected_runtime(tasks):
    expected_time = 0
    for task in tasks:
        expected_time += int(task["duration"])
    return expected_time
    
if __name__ == "__main__":
    args = parse_args()
    tasks = read_tasks(args.file)

    if args.dry_run:
        print(f"Expected duration time: {expected_runtime(tasks)} ")
    else:
        for task in tasks:
            run_cmd(task["name"])