"""Run a real SQL benchmark and save its measured samples. No data generation here."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shlex

import psycopg


def write_report(report, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "benchmark.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)
    lines = ["# Measured SQL contact generation benchmark", "",
        f"Recorded (UTC): {report['recorded_at']}", "",
        f"Environment: {report['environment']}; PostgreSQL {report['postgres_version']}; "
        f"client Python {report['python_version']}.", "",
        "| Locale | Users/run | Runs | Median users/second | Pooled users/second | Measured seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for result in report["results"]:
        lines.append(f"| {result['locale']} | {result['users_per_run']:,} | {len(result['runs'])} | "
            f"{result['median_users_per_second']:.2f} | {result['pooled_users_per_second']:.2f} | {result['total_seconds']:.6f} |")
    parameters = report["parameters"]
    lines += ["", f"Seed: `{parameters['seed']}`. Batch size: {parameters['batch_size']}. "
        f"One validation batch and {parameters['warmup_batches']} warmup batches per locale are excluded.", "",
        "Each measured loop calls the production `faker.generate_batch` procedure, generates all contact fields, "
        "assembles the complete batch JSON, and checks the actual JSON array length. No data is persisted or memoized. "
        "PostgreSQL `clock_timestamp()` measures elapsed wall time inside the SQL procedure. "
        "HTTP, HTML rendering, connection setup, and network transfer are excluded. "
        "Repeats reuse the deterministic workload with warmed database buffers; they still generate every contact again.", "",
        "## Individual measured runs", "",
        "| Locale | Run | Generated users | Seconds | Users/second |", "| --- | ---: | ---: | ---: | ---: |"]
    for result in report["results"]:
        for run in result["runs"]:
            lines.append(f"| {result['locale']} | {run['run']} | {run['users']:,} | {run['seconds']:.6f} | {run['users_per_second']:.2f} |")
    command = shlex.join(["docker", "compose", "exec", "-T", "api", "python", "-m", "app.benchmark",
        "--locales", *[result["locale"] for result in report["results"]],
        "--seed", parameters["seed"], "--users", str(parameters["users"]),
        "--batch-size", str(parameters["batch_size"]), "--repetitions", str(parameters["repetitions"]),
        "--warmup-batches", str(parameters["warmup_batches"]), "--output-dir", "/app/reports"])
    lines += ["", "The JSON report contains unrounded sample values. Rates depend on hardware, load, batch size, "
        "PostgreSQL version, and reference data. These numbers describe this recorded run, not a universal service guarantee.", "",
        "Reproduce:", "", "```sh", command, "```", ""]
    (output_dir / "benchmark.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locales", nargs="+", default=["en_US", "de_DE"])
    parser.add_argument("--seed", default="task6-benchmark-v1")
    parser.add_argument("--users", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--warmup-batches", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=Path(os.getenv("BENCHMARK_REPORT_DIR", "reports")))
    parser.add_argument("--environment", default="local Docker PostgreSQL (Linux container)")
    args = parser.parse_args(argv)
    report = dict(recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        environment=args.environment, python_version=platform.python_version(),
        parameters=dict(seed=args.seed, users=args.users, batch_size=args.batch_size,
                        repetitions=args.repetitions, warmup_batches=args.warmup_batches), results=[])
    # This explicit offline command can be long-running; public API queries stay capped at 15s.
    with psycopg.connect(os.getenv("DATABASE_URL", "postgresql://faker:faker@localhost:5432/faker"),
                         connect_timeout=10, options="-c statement_timeout=1800000 -c timezone=UTC", autocommit=True) as connection:
        report["postgres_version"] = connection.execute("SHOW server_version").fetchone()[0]
        report["postgres_build"] = connection.execute("SELECT version()").fetchone()[0]
        for locale in args.locales:
            print(f"Measuring {locale}: {args.users:,} complete users × {args.repetitions} runs...", flush=True)
            result = connection.execute("CALL faker.benchmark_users(%s,%s,%s,%s,%s,%s,NULL)",
                (locale, args.seed, args.users, args.batch_size, args.repetitions, args.warmup_batches)).fetchone()[0]
            report["results"].append(result)
            print(f"{locale}: median {result['median_users_per_second']:.2f} users/second", flush=True)
    report["completed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_report(report, args.output_dir)
    print(f"Saved {args.output_dir / 'benchmark.json'} and benchmark.md", flush=True)


if __name__ == "__main__":
    main()
