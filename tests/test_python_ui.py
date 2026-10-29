"""Acceptance checks against actual SQL results and server-rendered pages."""

import csv
import io
from html import unescape
from html.parser import HTMLParser

import pytest


pytestmark = pytest.mark.live


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.links = []
        self.forms = []
        self.textarea = ""
        self.in_textarea = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs)
        elif tag == "form":
            self.forms.append(attrs)
        elif tag == "textarea":
            self.in_textarea = True

    def handle_endtag(self, tag):
        if tag == "textarea":
            self.in_textarea = False

    def handle_data(self, data):
        if self.in_textarea:
            self.textarea += data


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_main_html_contains_sql_contacts_and_safe_get_navigation(api, locale):
    args = dict(locale=locale, seed='<script>"Grüße & 42"</script>', batch=7, batch_size=3)
    expected = api.users(**args)
    status, mime, html = api.get_text("/", **args)
    assert status == 200 and mime == "text/html"
    assert args["seed"] not in html and "&lt;script&gt;" in html
    assert "_next" not in html and "react" not in html.lower()
    for person in expected["users"]:
        for key in ("full_name", "address", "phone", "email", "eye_color"):
            assert person[key] in unescape(html)
        assert f'{person["height_cm"]} cm' in html
        assert f'{person["weight_kg"]} kg' in html
    page = Page(html)
    assert page.forms[0]["method"] == "get"
    active_url = next(link["href"] for link in page.links if link.get("aria-current") == "page")
    from urllib.parse import parse_qs, urlsplit
    assert parse_qs(urlsplit(active_url).query)["seed"] == [args["seed"]]
    next_url = next(link["href"] for link in page.links if link.get("aria-label") == "Next batch")
    assert parse_qs(urlsplit(next_url).query) == {
        "locale": [locale], "seed": [args["seed"]], "batch": ["8"], "batch_size": ["3"],
    }


def test_last_contact_page_has_no_next_link(api):
    _, _, html = api.get_text("/", batch=33333, batch_size=30)
    assert "1,000,000" in html
    assert not any(link.get("aria-label") == "Next batch" for link in Page(html).links)


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_text_is_rendered_by_python_and_matches_sql(api, locale):
    args = dict(locale=locale, seed="SSR text", position=9, word_count=120)
    expected = api.get("/api/text", **args)[1]
    status, mime, html = api.get_text("/text", **args)
    assert status == 200 and mime == "text/html"
    assert Page(html).textarea == expected["text"]
    assert "Sample 9" in html
    assert "_next" not in html


def test_csv_export_matches_the_applied_batch(api):
    args = dict(locale="de_DE", seed="csv-test", batch=4, batch_size=10)
    expected = api.users(**args)["users"]
    status, mime, content = api.get_text("/export.csv", **args)
    assert status == 200 and mime == "text/csv"
    rows = list(csv.DictReader(io.StringIO(content.lstrip("\ufeff"))))
    assert len(rows) == 10
    for row, person in zip(rows, expected):
        for key in ("full_name", "address", "email", "eye_color"):
            assert row[key] == person[key]
        # Phone strings intentionally receive spreadsheet formula protection.
        assert row["phone"] == "'" + person["phone"]
        assert float(row["latitude"]) == person["latitude"]


def test_switching_generators_remembers_each_applied_query(api):
    from http.cookiejar import CookieJar
    from urllib.parse import parse_qs, urlencode, urlsplit
    from urllib.request import HTTPCookieProcessor, build_opener
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    contacts = dict(locale="de_DE", seed="Remember & Grüße", batch=3, batch_size=25)
    with opener.open(api.base_url + "/?" + urlencode(contacts), timeout=30) as response:
        assert response.status == 200
    with opener.open(api.base_url + "/text?locale=en_US&seed=text-state&position=8&word_count=70", timeout=30) as response:
        page = Page(response.read().decode("utf-8"))
    url = next(link["href"] for link in page.links if link.get("href", "").startswith("/?"))
    assert parse_qs(urlsplit(url).query) == {key: [str(value)] for key, value in contacts.items()}
    with opener.open(api.base_url + url, timeout=30) as response:
        page = Page(response.read().decode("utf-8"))
    text_url = next(link["href"] for link in page.links if link.get("href", "").startswith("/text?"))
    assert parse_qs(urlsplit(text_url).query)["position"] == ["8"]


def test_benchmark_page_displays_the_actual_saved_samples(api):
    from statistics import median
    status, report = api.get("/benchmark.json")
    _, _, html = api.get_text("/benchmark")
    if status == 404:
        assert "No benchmark has been recorded" in html
        return
    assert status == 200
    assert report["postgres_version"] and report["recorded_at"]
    for result in report["results"]:
        assert result["locale"] in html
        assert result["total_generated"] == sum(run["users"] for run in result["runs"])
        rates = [run["users"] / run["seconds"] for run in result["runs"]]
        assert result["median_users_per_second"] == pytest.approx(median(rates))
        assert f'{result["median_users_per_second"]:.2f}' in html
