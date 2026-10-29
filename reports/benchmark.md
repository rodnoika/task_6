# Measured SQL contact generation benchmark

Recorded (UTC): 2026-10-29T21:18:27+00:00

Environment: Neon PostgreSQL (AWS us-east-2; direct connection); PostgreSQL 18.6 (4e5fd08); client Python 3.12.10.

| Locale | Users/run | Runs | Median users/second | Pooled users/second | Measured seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| en_US | 10,000 | 3 | 1657.88 | 1659.95 | 18.072814 |
| de_DE | 10,000 | 3 | 1448.96 | 1458.04 | 20.575613 |

Seed: `task6-benchmark-v1`. Batch size: 100. One validation batch and 5 warmup batches per locale are excluded.

Each measured loop calls the production `faker.generate_batch` procedure, generates all contact fields, assembles the complete batch JSON, and checks the actual JSON array length. No data is persisted or memoized. PostgreSQL `clock_timestamp()` measures elapsed wall time inside the SQL procedure. HTTP, HTML rendering, connection setup, and network transfer are excluded. Repeats reuse the deterministic workload with warmed database buffers; they still generate every contact again.

## Individual measured runs

| Locale | Run | Generated users | Seconds | Users/second |
| --- | ---: | ---: | ---: | ---: |
| en_US | 1 | 10,000 | 5.999704 | 1666.75 |
| en_US | 2 | 10,000 | 6.031786 | 1657.88 |
| en_US | 3 | 10,000 | 6.041324 | 1655.27 |
| de_DE | 1 | 10,000 | 6.916910 | 1445.73 |
| de_DE | 2 | 10,000 | 6.757217 | 1479.90 |
| de_DE | 3 | 10,000 | 6.901486 | 1448.96 |

The JSON report contains unrounded sample values. Rates depend on hardware, load, batch size, PostgreSQL version, and reference data. These numbers describe this recorded run, not a universal service guarantee.

Reproduce:

```sh
python scripts/benchmark.py --locales en_US de_DE --seed task6-benchmark-v1 --users 10000 --batch-size 100 --repetitions 3 --warmup-batches 5 --environment 'Neon PostgreSQL (AWS us-east-2; direct connection)' --output-dir reports
```
