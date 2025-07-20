# task-sched

A command line tool to schedule and optionally run a series of tasks in parallel, according to a task list specification input in text.

## Run

### (Optional) Create environment:

```bash
python3 -m venv --system-site-packages ./.venv
source ./.venv/bin/activate
```
### Install dependencies
```bash
pip install -r requirements
```

### Run tests:

```bash
python3 main.py tests/tasks.csv
```

## Usage

```bash
main.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--dry-run] file

positional arguments:
  file                  File containing the data to process.

options:
  -h, --help            show this help message and exit
  --serial              Run tasks one by one in the file order.
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level (default: CRITICAL).
  --dry-run             Validate the input task list and output the expected total runtime.
```

> [!NOTE]
> Use `--dry-run` to validate the input task list and output the expected total runtime without running the tasks.
> 
> Use `--log-level=INFO` to run the tasks and determine the difference in the actual runtime versus the expected runtime.

## Tests

Batch| Serial - Expected  | Serial - Real  || Parallel - Expected |Parallel - Real |Parallel - Difference|
|-|-|-|-|-|-|-|
tasks.csv| 12.00| 12.02|| 6.00 |7.01 | 1.01|
tasks2.csv| 7.00| 7.01|| 4.00 |4.00 | 0.004|
tasks3.csv| 13.00| 13.02|| 8.00 |10.01 | 2.01|
tasks_cycle.csv| 18.00| 18.02|| 10.00 |13.01 | 3.01|
tasks_cycle2.csv| 18.00| 18.03|| 14.00 |14.02 | 0.02|
tasks_cycle3.csv| 30.00| 30.04|| 16.00 |16.02 | 0.02|


## Notes:

- Python is my go-to language for prototyping, thus my choice here. However, Go would probably be better suited for this exercise (`goroutines`), 
- I'm using the Python `threading` package, which is multithreaded but not multiprocessed. I opted for this instead of `multiprocessing` package mostly for simplicity. Since the goal of the exercise seemed to be exploring deadlocks, race conditions, dependencies, concurrency, etc., the `threading` package seemed to be enough.
- Again, for simplicity, I assumed the `task['name']` as UID. This could be easily changed. 
- There are two main reasons for the differences between Real and expected times:
  - Millisecond differences: The tasks are actually running I/O operations, and these operations' execution times are being disregarded.
  - Second differences: When using `threading`, we don't schedule the order of tasks; instead, we pass the dependency tree to the `threading` scheduler. The algorithm I'm using to find the critical path and compute the total duration time may differ from the algorithm used by the `threading` package. For a more precise estimate, I would need to study the source code and attempt to reproduce their approach here. 