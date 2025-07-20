import argparse
import logging
import csv
import subprocess
import time
import threading
from collections import defaultdict
import networkx as nx
import sys

TASKS_PATH = "./tests/tasks/"


def parse_args() -> argparse.Namespace:
    """Parse args

    Returns:
        argparse.Namespace: Parsed args
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("file", help="File containing the data to process.")
    parser.add_argument(
        "--serial",
        action="store_true",
        default=False,
        help="Run tasks one by one in the file order.",
    )
    parser.add_argument(
        "--log-level",
        default="CRITICAL",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: CRITICAL).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate the input task list and output the expected total runtime.",
    )

    return parser.parse_args()


def read_tasks(filepath: str) -> csv.DictReader:
    """Read a `.csv` file from the given path.

    Args:
        filepath (str): path to the file.

    Returns:
        csv.DictReader: Dictionary with the csv contents.
    """
    with open(filepath, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        logging.debug("Tasks loaded")
        return list(reader)


def get_dependencies(task: dict) -> set:
    """Given a single task row, parse the `dependencies` key and return a set of values.

    Args:
        task (dict): Task

    Returns:
        set: Dependencies
    """
    return set(task["dependencies"].split("-"))


def get_task_by_name(task_name: str, tasks: csv.DictReader) -> dict:
    """Given a str `task_name` return the full row (name, duration, dependencies) from the tasks list.

    Args:
        task_name (str): Task name
        tasks (csv.DictReader): List of tasks

    Returns:
        dict: task
    """
    for task in tasks:
        if task_name == task["name"]:
            return task


def get_all_dependencies(tasks: csv.DictReader) -> set:
    """Return all dependeices for all tasks in the original list.

    Args:
        tasks (csv.DictReader): Tasks

    Returns:
        set: Dependencies
    """
    dependencies = set()
    for task in tasks:
        for resource in get_dependencies(task):
            dependencies.add(resource)
    return dependencies


def find_faster_by_name(tasks: csv.DictReader, tasks_names: list) -> str:
    """Find the fastest task in a sub-group of tasks. Returns the tasks["name"].

    Args:
        tasks (csv.DictReader): Full list of tasks
        tasks_names (list): Subgroup where it looks for

    Returns:
        str: Name of the fastest task
    """
    faster = ""
    faster_duration = sys.maxsize
    for name in tasks_names:
        for task in tasks:
            if name == task["name"]:
                current = min(faster_duration, int(task["duration"]))
                if current < faster_duration:
                    faster_duration = current
                    faster = task["name"]
    return faster


def is_mono_dependent(task: dict) -> bool:
    """Return true is task has only one dependency

    Args:
        task (dict): Task

    Returns:
        bool: True if task has only one dependency
    """
    return len(get_dependencies(task)) == 1


def dependency_graph(tasks: csv.DictReader) -> defaultdict:
    """Build up an optimized dependency graph. It may create cycled graphs, though.

    Args:
        tasks (csv.DictReader): Tasks

    Returns:
        defaultdict: Dependency Graph
    """
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


## If cycles are found in the dependency graph
## remove them by doing the dependent tasks one by one
def dependency_cycled_graph(tasks: csv.DictReader) -> defaultdict:
    """In case the prefered dependency_graph function had created
    a cycled graph, this function is an option to avoid the cycles.
    It will manage to run all dependent tasks in order, reduncing the
    performance

    Args:
        tasks (csv.DictReader): Tasks

    Returns:
        defaultdict: Dependency Graph
    """
    logging.debug("Generating alternative dependency graph")
    dependency_graph = defaultdict(set)
    previous_writer = {}

    for task in tasks:
        for dependency in get_dependencies(task):
            if dependency not in previous_writer:
                previous_writer[dependency] = task["name"]

    logging.debug("Primary tasks by dependency: ")
    for k, v in previous_writer.items():
        logging.debug(f" {k} : {v}")

    for task in tasks:
        for dependency in get_dependencies(task):
            writer = previous_writer.get(dependency)
            if writer and writer != task["name"]:
                dependency_graph[task["name"]].add(writer)
                previous_writer[dependency] = task["name"]

    logging.debug("Task Dependencies: ")
    for task, deps in dependency_graph.items():
        logging.debug(f"    {task} depends on: {', '.join(deps)}")

    return dependency_graph


def run_cmd(
    command: str, ready_events: list = None, done_event: threading.Event = None
):
    """Check if the dependencies are ready, run the command, finnaly mark it as done

    Args:
        command (str): Command
        ready_events (list, optional): Dependency list. Defaults to None.
        done_event (threading.Event, optional): Done flag. Defaults to None.
    """
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


def check_cycles(tasks: csv.DictReader, dependencies: defaultdict) -> bool:
    """Check if the Dependency Graph is a cycled graph.

    Args:
        tasks (csv.DictReader): Tasks
        dependencies (defaultdict): Dependency Graph

    Returns:
        bool: Is a cycled Graph?
    """
    try:
        build_DiGraph(tasks, dependencies)
        return False
    except nx.NetworkXUnfeasible:
        logging.critical(
            "Cycles detected. Running alternative dependecy builder. Expect impact in performance"
        )
        return True


def run_taks(tasks: csv.DictReader, serial: bool):
    """Run all Tasks in aserial or parallel

    Args:
        tasks (csv.DictReader): Tasks
        serial (bool): Should it run serial?
    """
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
    logging.info(
        f"Difference between execution and expected time: {duration - expected}"
    )


def run_parallel(tasks: csv.DictReader):
    """Run all tasks in parallel

    Args:
        tasks (csv.DictReader): Tasks
    """
    dependencies = dependency_graph(tasks)  # Try the optimized dependency builder
    if check_cycles(tasks, dependencies):
        dependencies = dependency_cycled_graph(
            tasks
        )  # Use the sub-optimal, if finds cycles in dependency graph
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


def run_serial(tasks: csv.DictReader):
    """Run all tasks one by one in order

    Args:
        tasks (csv.DictReader): Tasks
    """
    for task in tasks:
        run_cmd(task["name"])


def get_durations(tasks: csv.DictReader) -> dict:
    """Get durations for each task

    Args:
        tasks (csv.DictReader): Tasks

    Returns:
        _type_: Dictionary with key=names and values=durations
    """
    return {task["name"]: task["duration"] for task in tasks}


def build_DiGraph(tasks: csv.DictReader, dependencies: defaultdict) -> nx.digraph:
    """Build a DiGraph (Directed graphs with self loops) from the dependencies graph.

    Args:
        tasks (csv.DictReader): Tasks
        dependencies (defaultdict): Dependency graph

    Returns:
        nx.digraph: directed graph
    """
    graph = nx.DiGraph()
    durations = get_durations(tasks)

    for task, deps in dependencies.items():
        for dep in deps:
            graph.add_edge(dep, task)

    for task in tasks:
        if task not in list(nx.topological_sort(graph)):
            graph.add_node(task["name"])

    nx.set_node_attributes(graph, durations, "duration")
    return graph


def critical_path(tasks: csv.DictReader) -> int:
    """Find the critical path (the most time consumind path in the directed graph)
    and return the duration

    Args:
        tasks (csv.DictReader): Tasks

    Returns:
        int: Duration
    """
    dependencies = dependency_graph(tasks)
    if check_cycles(tasks, dependencies):
        dependencies = dependency_cycled_graph(tasks)
    graph = build_DiGraph(tasks, dependencies)
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
            longest_paths[node] = min(longest_paths[p] for p in predecessors) + int(
                durations[node]
            )

    return max(longest_paths.values())


def expected_runtime(tasks: csv.DictReader, serial: bool) -> int:
    """Return the expected time for running all the tasks

    Args:
        tasks (csv.DictReader): Tasks
        serial (bool): Should it run serial?

    Returns:
        int: Duration
    """
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
