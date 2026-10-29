"""SQL integration checks for the generator's data and procedural boundary."""

import pytest


pytestmark = pytest.mark.database


def test_generator_schema_has_only_procedures_for_custom_routines(db_connect):
    with db_connect() as connection:
        routines = connection.execute(
            "SELECT p.proname, p.prokind FROM pg_proc p "
            "JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'faker'"
        ).fetchall()
    assert any(name == "generate_batch" and kind == "p" for name, kind in routines), routines
    assert all(kind == "p" for _, kind in routines), routines
    assert len(routines) >= 4, "Random, normal, sphere and record generation must be modular procedures"


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_lookup_data_has_sufficient_capacity_without_duplicate_values(db_connect, locale):
    minimums = {
        "first_name": 100,
        "last_name": 100,
        "street_stem": 100,
        "street_suffix": 4,
        "title": 4,
        "eye_color": 6,
        "address_format": 3,
        "phone_format": 3,
    }
    with db_connect() as connection:
        counts = {
            kind: (total, distinct)
            for kind, total, distinct in connection.execute(
                "SELECT kind, count(*), count(DISTINCT value) "
                "FROM faker.lookup_values WHERE locale = %s GROUP BY kind", (locale,)
            )
        }
        city_count, city_distinct = connection.execute(
            "SELECT count(*), count(DISTINCT (name, region, postal_code)) "
            "FROM faker.cities WHERE locale = %s", (locale,)
        ).fetchone()
    for kind, minimum in minimums.items():
        assert kind in counts, (locale, kind, counts)
        total, distinct = counts[kind]
        assert distinct >= minimum, (locale, kind, distinct, minimum)
        assert total == distinct, (locale, kind, "Duplicate reference rows reduce useful variety")
    assert city_count >= 50 and city_distinct >= 50, (locale, city_count, city_distinct)


def test_different_database_sessions_and_mixed_batches_reproduce_positions(sql_users):
    reference = sql_users(seed="sql-session-replay", batch_size=100)["users"]
    sql_users(locale="de_DE", seed="other", batch=400)
    sql_users(seed="sql-session-replay", batch=45, batch_size=2)
    assert sql_users(seed="sql-session-replay", batch_size=100)["users"] == reference
    assert sql_users(seed="sql-session-replay", batch=10, batch_size=7)["users"] == reference[70:77]
    assert sql_users(seed="different", batch_size=100)["users"] != reference


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_api_exposes_the_actual_sql_batch(api, sql_users, locale):
    params = {"locale": locale, "seed": "api-sql-boundary", "batch": 37, "batch_size": 9}
    assert api.users(**params) == sql_users(**params)
