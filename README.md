# task-sched

A command line tool to schedule and optionally run a series of tasks in parallel, according to a task list specification input in text.

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
> Use `--log-level=INFO` to run the tasks and determine the difference in the actual runtime versus the expected runtime.


## Assumptions:

- Concurrency vs Maultiprocessing
- Task name as UID