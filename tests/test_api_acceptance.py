"""Public API acceptance tests, derived from the task rather than implementation."""

import concurrent.futures
from html.parser import HTMLParser
import math
import re

import pytest


pytestmark = pytest.mark.live

FIELDS = {
    "position", "full_name", "address", "latitude", "longitude", "height_cm",
    "weight_kg", "eye_color", "phone", "email",
}


def assert_record(record):
    assert FIELDS <= record.keys(), record
    assert isinstance(record["position"], int) and not isinstance(record["position"], bool)
    for field in ("full_name", "address", "eye_color", "phone", "email"):
        assert isinstance(record[field], str) and record[field].strip(), (field, record)
    assert re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", record["email"]), record
    for field in ("latitude", "longitude", "height_cm", "weight_kg"):
        assert isinstance(record[field], (int, float)) and not isinstance(record[field], bool)
        assert math.isfinite(record[field]), (field, record)
    assert -90 <= record["latitude"] <= 90
    assert -180 <= record["longitude"] <= 180
    assert 0 < record["height_cm"] < 300
    assert 0 < record["weight_kg"] < 500


def test_supported_locales_have_country_metadata(api):
    status, payload = api.get("/api/locales")
    assert status == 200
    locales = {item["code"]: item for item in payload["locales"]}
    assert {"en_US", "de_DE"} <= locales.keys()
    for locale in ("en_US", "de_DE"):
        assert locales[locale]["label"].strip()
        assert locales[locale]["country"].strip()


def test_omitted_arguments_produce_the_documented_first_ten_people(api):
    status, payload = api.get("/api/users")
    assert status == 200
    assert payload["locale"] == "en_US" and payload["seed"] == "42"
    assert payload["batch"] == 0 and payload["batch_size"] == 10
    assert [row["position"] for row in payload["users"]] == list(range(1, 11))


class PreviewTable(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag == "td":
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag == "td":
            self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.row:
            self.rows.append(self.row)


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_python_html_preview_renders_all_sql_fields_and_escapes_seed(api, locale):
    params = {"locale": locale, "seed": '<script>alert("seed")</script>', "batch": 0, "batch_size": 3}
    expected = api.users(**params)["users"]
    status, content_type, html = api.get_text("/preview", **params)
    assert status == 200 and content_type == "text/html"
    assert '<script>alert("seed")</script>' not in html
    assert "&lt;script&gt;" in html
    table = PreviewTable()
    table.feed(html)
    columns = ("position", "full_name", "address", "latitude", "longitude", "height_cm", "weight_kg", "eye_color", "phone", "email")
    assert table.rows == [[str(person[key]) for key in columns] for person in expected]


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_first_and_next_batches_are_contiguous(api, locale):
    first = api.users(locale=locale)
    second = api.users(locale=locale, batch=1)
    for index, payload in enumerate((first, second)):
        assert payload["locale"] == locale
        assert str(payload["seed"]) == "42"
        assert payload["batch"] == index
        assert payload["batch_size"] == 10
        assert payload["total"] == 1_000_000
        assert payload["has_next"] is True
        assert [row["position"] for row in payload["users"]] == list(range(index * 10 + 1, index * 10 + 11))
        for row in payload["users"]:
            assert_record(row)
    assert first["users"] != second["users"]


def test_position_is_independent_of_batch_size_and_request_order(api):
    reference = api.users(seed="position-invariant", batch_size=100)["users"]
    for batch in (9, 0, 5, 1):
        actual = api.users(seed="position-invariant", batch=batch, batch_size=10)["users"]
        assert actual == reference[batch * 10 : batch * 10 + 10]
    assert api.users(seed="position-invariant", batch=17, batch_size=3)["users"] == reference[51:54]


def test_interleaved_seeds_and_locales_cannot_change_previous_records(api):
    baseline = api.users(seed="repeatable")["users"]
    different_seed = api.users(seed="another-seed")["users"]
    german = api.users(locale="de_DE", seed="repeatable")["users"]
    api.users(locale="de_DE", seed="another-seed", batch=77)
    api.users(seed="repeatable", batch=90, batch_size=7)
    assert api.users(seed="repeatable")["users"] == baseline
    assert different_seed != baseline
    assert german != baseline
    # Compare generated fields, not the position column, for separation.
    assert any(a["full_name"] != b["full_name"] for a, b in zip(baseline, different_seed))
    assert any(a["address"] != b["address"] for a, b in zip(baseline, german))


def test_random_key_distinguishes_ambiguous_seed_position_pairs_and_long_seeds(api):
    # Naive concatenation of seed and zero-based position maps both to a123.
    first = api.users(seed="a1", batch=23, batch_size=1)["users"][0]
    second = api.users(seed="a12", batch=3, batch_size=1)["users"][0]
    generated_fields = FIELDS - {"position"}
    assert {key: first[key] for key in generated_fields} != {key: second[key] for key in generated_fields}
    first_long = api.users(seed="x" * 63 + "a")["users"]
    second_long = api.users(seed="x" * 63 + "b")["users"]
    assert first_long != second_long


def test_concurrent_requests_preserve_each_stream(api):
    cases = [
        {"locale": "en_US", "seed": "parallel-a", "batch": 2, "batch_size": 10},
        {"locale": "de_DE", "seed": "parallel-b", "batch": 7, "batch_size": 10},
        {"locale": "en_US", "seed": "parallel-b", "batch": 0, "batch_size": 10},
    ]
    expected = [api.users(**case) for case in cases]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        actual = list(pool.map(lambda case: api.users(**case), cases))
    assert actual == expected


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_final_partial_batch_and_millionth_position(api, locale):
    partial = api.users(locale=locale, seed="million", batch=33_333, batch_size=30)
    assert partial["total"] == 1_000_000
    assert partial["has_next"] is False
    assert [row["position"] for row in partial["users"]] == list(range(999_991, 1_000_001))
    final = api.users(locale=locale, seed="million", batch=999_999, batch_size=1)
    assert final["users"] == partial["users"][-1:]
    assert final["has_next"] is False
    for row in partial["users"]:
        assert_record(row)


@pytest.mark.parametrize("overrides", [
    {"locale": "fr_FR"}, {"locale": ""},
    {"seed": ""}, {"seed": "x" * 65},
    {"batch": -1}, {"batch": "oops"}, {"batch": 1.5}, {"batch": 100_000},
    {"batch_size": 0}, {"batch_size": -1}, {"batch_size": 101},
    {"batch_size": "oops"},
])
def test_invalid_inputs_are_rejected(api, overrides):
    params = {"locale": "en_US", "seed": "42", "batch": 0, "batch_size": 10}
    params.update(overrides)
    status, payload = api.get("/api/users", **params)
    assert status == 422, (params, status, payload)
    assert payload.get("detail"), payload


@pytest.mark.parametrize("seed", ["0", "-1", "x" * 64, "O'Reilly", "Grüße & space + seed"])
def test_valid_seed_strings_are_repeatable_and_preserved(api, seed):
    first = api.users(seed=seed, batch_size=2)
    assert str(first["seed"]) == seed
    assert api.users(seed=seed, batch_size=2) == first


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_localized_contact_formats_and_variation(api, locale):
    rows = api.users(locale=locale, seed="format-and-variety", batch_size=100)["users"]
    for row in rows:
        assert_record(row)
        if locale == "en_US":
            assert row["phone"].startswith("+1"), row["phone"]
            assert re.search(r"\b\d{5}(?:-\d{4})?\b", row["address"]), row["address"]
        else:
            assert row["phone"].startswith("+49"), row["phone"]
            assert re.search(r"\b\d{5}\b", row["address"]), row["address"]
    assert len({row["full_name"] for row in rows}) >= 50
    assert len({row["address"] for row in rows}) >= 90
    assert len({row["phone"] for row in rows}) >= 90
    assert len({re.sub(r"\d+", "#", row["phone"]) for row in rows}) >= 2
    assert len({row["email"] for row in rows}) >= 90
    assert len({row["eye_color"] for row in rows}) >= 3
    assert len({len(row["full_name"].split()) for row in rows}) >= 2
