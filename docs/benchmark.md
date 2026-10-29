# Benchmark complete SQL contact generation

The benchmark measures real fake-user generation in **users/second**, separately for `en_US` and `de_DE`. The [recorded report](../reports/benchmark.md) is accompanied by [unrounded JSON samples](../reports/benchmark.json). The Python interface displays the same saved report at `/benchmark`; it does not show a fabricated speed or time a page load.

## Reproduce

Start the application, install `database/005_benchmark.sql` if upgrading an existing database, then run:

```sh
docker compose exec -T api python -m app.benchmark --users 10000 --batch-size 100 --repetitions 3 --warmup-batches 5 --output-dir /app/reports
```

The Compose mount persists both files in the repository's `reports/` folder. No API endpoint runs a costly benchmark just because a visitor opens a page. For native Python, use `python scripts/benchmark.py` with the same options and a configured `DATABASE_URL`; add `--environment 'native PostgreSQL on ...'` to describe the actual setup.

## SQL API

```sql
CALL faker.benchmark_users('en_US', 'task6-benchmark-v1', 10000, 100, 3, 5, NULL);
```

| Argument | Type | Description |
| --- | --- | --- |
| `p_locale` | text | Existing locale; benchmark each locale separately. |
| `p_seed` | text | Exact seed of 1–64 characters, with at least one non-whitespace character. |
| `p_users` | integer, default 10000 | Users **per measured run**, 100–1,000,000; must be a multiple of batch size. |
| `p_batch_size` | integer, default 100 | Production batch size, 1–100. |
| `p_repetitions` | integer, default 3 | Number of measured runs, 1–10. |
| `p_warmup_batches` | integer, default 5 | Unmeasured warmup batches per locale, 0–100. |
| `p_result` | INOUT jsonb, default NULL | Raw measured runs, counts, seconds, median and pooled throughput, and arguments. |

One initial validation batch checks locale and seed, followed by the configured warmup. Both are excluded from the timer. Each measured run calls the actual production `faker.generate_batch` for positions 1 through `p_users`. Each batch creates all ten fields, including normally distributed physical attributes, spherical coordinates, formatted contacts, and complete JSON output. Actual `jsonb_array_length` values are summed; a wrong total aborts the benchmark.

Time is the difference between two [PostgreSQL `clock_timestamp()` calls](https://www.postgresql.org/docs/17/functions-datetime.html#FUNCTIONS-DATETIME-CURRENT), which advance inside a statement. Using transaction-stable `now()` would be invalid here. Included work: full SQL generation, batch JSON assembly, procedure-call loop, and counting returned users. Excluded work: connection setup, network transfer of batches, HTTP, CSV, HTML and browser rendering. This is database generation throughput, not an end-to-end browser benchmark.

For each run, `users_per_second = actual_users / elapsed_seconds`. The main result is the median of individual run rates. Pooled throughput is `sum(actual_users) / sum(elapsed_seconds)` and is reported separately. Raw seconds and rates are preserved without display rounding in JSON.

Repeats use the same deterministic workload. There is no cache of generated contacts: every procedure call regenerates every field. Reference dictionaries and query plans can benefit from warm database buffers. No fake users are inserted into tables.

## Limits and interpretation

Hardware, PostgreSQL version, other machine activity, warmed buffers, lookup data and batch size affect the result. A report describes its recorded environment and time; do not present it as a guaranteed capacity of every deployment. The Python CLI defaults to a local Docker environment label; override `--environment` when running elsewhere. The command uses a 30-minute statement timeout independently of the public API's 15-second query timeout.

The JSON includes PostgreSQL version/build, Python version, generator version, parameters, start/completion timestamps and every measured sample. No credentials or database URL are written to reports. Copy the report with your submission rather than quoting a result from a different environment.
