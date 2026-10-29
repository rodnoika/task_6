"""A real SQL benchmark must count generated users and report actual elapsed time."""

import pytest


pytestmark = pytest.mark.database


def test_sql_benchmark_measures_complete_batches(db_connect):
    with db_connect() as connection:
        report = connection.execute(
            "CALL faker.benchmark_users(%s,%s,%s,%s,%s,%s,NULL)",
            ("en_US", "qa-benchmark", 100, 25, 2, 1),
        ).fetchone()[0]
    assert report["total_generated"] == 200
    assert report["users_per_run"] == 100
    assert report["warmup_batches"] == 1
    assert report["batch_size"] == 25
    assert len(report["runs"]) == 2
    rates = []
    for run in report["runs"]:
        assert run["users"] == 100
        assert run["seconds"] > 0
        assert run["users_per_second"] == pytest.approx(100 / run["seconds"], rel=1e-8)
        rates.append(run["users_per_second"])
    assert report["median_users_per_second"] == pytest.approx(sum(rates) / 2)
    assert report["pooled_users_per_second"] == pytest.approx(
        200 / sum(run["seconds"] for run in report["runs"])
    )


@pytest.mark.parametrize("users,size,reps,warmup", [(99, 10, 1, 0), (101, 10, 1, 0),
    (100, 101, 1, 0), (100, 10, 0, 0), (100, 10, 1, -1)])
def test_sql_benchmark_rejects_misleading_or_unbounded_arguments(db_connect, users, size, reps, warmup):
    import psycopg
    with db_connect() as connection, pytest.raises(psycopg.errors.InvalidParameterValue):
        connection.execute("CALL faker.benchmark_users(%s,%s,%s,%s,%s,%s,NULL)",
            ("en_US", "qa", users, size, reps, warmup))
