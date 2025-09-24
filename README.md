# task-sched

A command line tool to schedule and optionally run a series of tasks in parallel, according to a task list specification input in text.

## Run

### Install dependencies
```bash
uv sync
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
tasks.csv| 12.00| 12.02|| 7.00 |7.01 | 0.009|
tasks2.csv| 7.00| 7.01|| 4.00 |4.00 | 0.004|
tasks3.csv| 13.00| 13.02|| 10.00 |10.01 | 0.01|
tasks_cycle.csv| 18.00| 18.02|| 13.00 |13.01 |  0.01|
tasks_cycle2.csv| 18.00| 18.03|| 14.00 |14.02 | 0.02|
tasks_cycle3.csv| 30.00| 30.04|| 16.00 |16.02 | 0.02|


## Notes:

- Python is my go-to language for prototyping, thus my choice here. However, Go would probably be better suited for this exercise (`goroutines`), 
- I'm using the Python `threading` package, which is multithreaded but not multiprocessed. I opted for this instead of `multiprocessing` package mostly for simplicity. Since the goal of the exercise seemed to be exploring deadlocks, race conditions, dependencies, concurrency, etc., the `threading` package seemed to be enough.
- Again, for simplicity, I assumed the `task['name']` as UID. This could be easily changed. 
- The reason for the millisecond differences between real and expected times is the I/O operations. The test tasks are simulating real tasks, but they are actually allocating the resources and performing I/O operations, and these operations' execution times are being disregarded.
  