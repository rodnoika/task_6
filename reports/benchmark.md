# Measured SQL contact generation benchmark

Recorded (UTC): 2026-10-29T18:53:32+00:00

Environment: local Docker PostgreSQL (Linux container); PostgreSQL 17.11; client Python 3.12.16.

| Locale | Users/run | Runs | Median users/second | Pooled users/second | Measured seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| en_US | 10,000 | 3 | 223.55 | 177.56 | 168.954433 |
| de_DE | 10,000 | 3 | 191.49 | 192.61 | 155.753605 |

Seed: `task6-benchmark-v1`. Batch size: 100. One validation batch and 5 warmup batches per locale are excluded.

Each measured loop calls the production `faker.generate_batch` procedure, generates all contact fields, assembles the complete batch JSON, and checks the actual JSON array length. No data is persisted or memoized. PostgreSQL `clock_timestamp()` measures elapsed wall time inside the SQL procedure. HTTP, HTML rendering, connection setup, and network transfer are excluded. Repeats reuse the deterministic workload with warmed database buffers; they still generate every contact again.

## Individual measured runs

| Locale | Run | Generated users | Seconds | Users/second |
| --- | ---: | ---: | ---: | ---: |
| en_US | 1 | 10,000 | 44.732141 | 223.55 |
| en_US | 2 | 10,000 | 44.013660 | 227.20 |
| en_US | 3 | 10,000 | 80.208632 | 124.67 |
| de_DE | 1 | 10,000 | 52.223320 | 191.49 |
| de_DE | 2 | 10,000 | 52.998628 | 188.68 |
| de_DE | 3 | 10,000 | 50.531657 | 197.90 |

The JSON report contains unrounded sample values. Rates depend on hardware, load, batch size, PostgreSQL version, and reference data. These numbers describe this recorded run, not a universal service guarantee.

Reproduce:

```sh
docker compose exec -T api python -m app.benchmark --locales en_US de_DE --seed task6-benchmark-v1 --users 10000 --batch-size 100 --repetitions 3 --warmup-batches 5 --output-dir /app/reports
```
