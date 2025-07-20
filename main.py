import argparse
import logging
import csv
import subprocess
import time
import threading
from collections import defaultdict
import networkx as nx
import sys

TASKS_PATH="./tests/tasks/"

def parse_args():
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "file", 
        help="File containing the data to process.")
    parser.add_argument(
        "--serial",
        action="store_true",
        default=False,
        help="Run tasks one by one in the file order."
    )
    parser.add_argument(
        "--log-level",
        default="CRITICAL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: CRITICAL)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate the input task list and output the expected total runtime."
    )
    
    return parser.parse_args()


def read_tasks(filepath):
    with open(filepath, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        logging.debug("Tasks loaded")
        return list(reader)


def get_dependencies(task):
    return set(task["dependencies"].split("-"))


def get_task_by_name(task_name, tasks):
    for task in tasks:
        if task_name == task["name"]:
            return task


def get_all_dependencies(tasks):
    dependencies = set()
    for task in tasks:
        for resource in get_dependencies(task):
            dependencies.add(resource)
    return dependencies


def find_faster_by_name(tasks, tasks_names):
    faster = ''
    faster_duration = sys.maxsize
    for name in tasks_names:
        for task in tasks:
            if name == task["name"]:
                current = min(faster_duration, int(task["duration"]))
                if current < faster_duration:
                    faster_duration = current
                    faster = task["name"]
    return faster


def is_mono_dependent(task):
    return len(get_dependencies(task)) == 1


def dependency_graph(tasks):
    dependency_graph = defaultdict(set)
    interested_parties = {}

    for task in tasks:
        for dependency in get_dependencies(task):
            if dependency not in interested_parties:
                interested_parties[dependency] = [task["name"]]
            else:
                interested_parties[dependency].append(task["name"])

    logging.debug("Interested parties by dependency: ")
    for dep, task in interested_parties.items():
        logging.debug(f" {dep} : {task}")

    for task in tasks:
        for dependency in get_dependencies(task):
            writers = interested_parties.get(dependency)
            for writer in writers:
                if writer != task["name"]:
                    dependency_graph[task["name"]].add(writer)

    dependencies = get_all_dependencies(tasks)
    
    # Removing faster and less dependent tasks from dependency_graph
    # it turns them into starters candidates. 
    for resource in dependencies:
        monodependents = []
        for task_name in interested_parties[resource]:
            if is_mono_dependent(get_task_by_name(task_name, tasks)):
                monodependents.append(task_name)
        removal_candidate = find_faster_by_name(tasks, monodependents)
        if removal_candidate in dependency_graph:
            del dependency_graph[removal_candidate]

    logging.debug("Task Dependencies: ")
    for task, deps in dependency_graph.items():
        logging.debug(f"    {task} depends on: {', '.join(deps)}")

    return dependency_graph


def run_cmd(command,ready_events=None, done_event=None):
    if ready_events:
        for ev in ready_events:
            ev.wait()
    try:
        subprocess.run([f"{TASKS_PATH}{command}"])
        logging.debug(f"Task {command} executed succefully")
    except subprocess.CalledProcessError:
        logging.error(f"Task {command} failed")
    if done_event:
        done_event.set()


def check_cycles(tasks):
    try:
        build_DiGraph(tasks)
    except nx.NetworkXUnfeasible:
        logging.critical("Cycle detected. Cannot determine a valid execution order")
        logging.critical("Exit code 1")
        sys.exit(1)


def run_taks(tasks, serial):
    start = time.time()
    if serial:
        logging.info("Serial execution")
        run_serial(tasks)
    else:
        logging.info("Parallel execution")
        run_parallel(tasks)

    end = time.time()
    duration = end - start
    expected = expected_runtime(tasks, serial)
    logging.info("All tasks executed succefully")
    logging.info(f"Execution duration time: {duration}")
    logging.info(f"Expected duration time: {expected}")
    logging.info(f"Difference between execution and expected time: {duration - expected}")

def run_parallel(tasks):
    check_cycles(tasks)
    dependencies =  dependency_graph(tasks)
    task_events = {task["name"]: threading.Event() for task in tasks}
    threads = []

    for task in tasks:
        name = task["name"]
        deps = dependencies[name]
        ready_events = [task_events[dep] for dep in deps]
        done_event = task_events[name]
        t = threading.Thread(target=run_cmd, args=(name, ready_events, done_event))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()


def run_serial(tasks):
    for task in tasks:
            run_cmd(task["name"])


def get_durations(tasks):
    return {task["name"]: task["duration"] for task in tasks}


def build_DiGraph(tasks):
    graph = nx.DiGraph()
    dependencies =  dependency_graph(tasks)
    durations = get_durations(tasks)

    for task, deps in dependencies.items():
        for dep in deps:
            graph.add_edge(dep,task)

    for task in tasks:
        if task not in list(nx.topological_sort(graph)):
            graph.add_node(task["name"])

    nx.set_node_attributes(graph, durations, 'duration')
    return graph


def critical_path(tasks):
    check_cycles(tasks)
    graph = build_DiGraph(tasks)
    longest_paths = {}
    durations = get_durations(tasks)

    # Plot dependency graph
    # import matplotlib.pyplot as plt
    # nx.draw(graph, with_labels=True, node_size=2000, arrows=True)
    # plt.show()

    for node in nx.topological_sort(graph):
        predecessors = list(graph.predecessors(node))
        if not predecessors:
            longest_paths[node] = int(durations[node])
        else:
            longest_paths[node] = min(longest_paths[p] for p in predecessors) + int(durations[node])

    return max(longest_paths.values())


def expected_runtime(tasks, serial):
    if serial:
        expected_time = 0
        for task in tasks:
            expected_time += int(task["duration"])
        return expected_time
    else:
        return critical_path(tasks)
    

if __name__ == "__main__":
    args = parse_args()

    logger = logging.getLogger()
    logger.setLevel(args.log_level)

    tasks = read_tasks(args.file)

    if args.dry_run:
        print(f"Expected duration time: {expected_runtime(tasks, args.serial)} ")
    else:
        run_taks(tasks, args.serial)