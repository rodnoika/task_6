"""Server-rendered primary interface. JavaScript only enhances local controls."""

import csv
import io
import json
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from .data import Batch, BatchSize, Locale, Seed, TextPosition, WordCount
from .data import generate_text, locales, users


router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters["number"] = lambda value: f"{value:,}"
templates.env.filters["coordinate"] = lambda value, positive, negative: f"{abs(value):.5f}° {positive if value >= 0 else negative}"


def page_url(path, **arguments):
    return path + "?" + urlencode(arguments)


def remembered_url(request, view):
    """Remember applied arguments across tabs; cookie data can only form local URLs."""
    path = "/" if view == "contacts" else "/text"
    keys = {"locale", "seed", "batch", "batch_size"} if view == "contacts" else {"locale", "seed", "position", "word_count"}
    raw = request.cookies.get("batchlab_" + view, "")
    arguments = {key: value for key, value in parse_qsl(raw[:512]) if key in keys}
    return page_url(path, **arguments) if arguments else path


def render(request, template, view, arguments=None, status_code=200, **context):
    values = {
        "view": view, "contacts_url": remembered_url(request, "contacts"),
        "text_url": remembered_url(request, "text"), **context,
    }
    if arguments:
        values["contacts_url" if view == "contacts" else "text_url"] = page_url(
            "/" if view == "contacts" else "/text", **arguments)
    response = templates.TemplateResponse(request=request, name=template, context=values, status_code=status_code)
    response.headers["Cache-Control"] = "no-store"
    if arguments:
        response.set_cookie("batchlab_" + view, urlencode(arguments), httponly=True,
                            samesite="lax", secure=request.url.scheme == "https", max_age=86400 * 30)
    return response


@router.get("/", response_class=HTMLResponse)
def contacts_page(request: Request, locale: Locale = "en_US", seed: Seed = "42", batch: Batch = 0, batch_size: BatchSize = 10):
    arguments = dict(locale=locale, seed=seed, batch=batch, batch_size=batch_size)
    result = users(**arguments)
    available = locales()["locales"]
    country = next(item["country"] for item in available if item["code"] == locale)
    sizes = sorted({10, 25, 50, 100, batch_size})
    return render(request, "contacts.html", "contacts", arguments,
        data=result, locales=available, country=country, sizes=sizes,
        export_url=page_url("/export.csv", **arguments),
        previous_url=page_url("/", **{**arguments, "batch": batch - 1}) if batch > 0 else None,
        next_url=page_url("/", **{**arguments, "batch": batch + 1}) if result["has_next"] else None)


@router.get("/text", response_class=HTMLResponse)
def text_page(request: Request, locale: Locale = "en_US", seed: Seed = "42", position: TextPosition = 1, word_count: WordCount = 80):
    arguments = dict(locale=locale, seed=seed, position=position, word_count=word_count)
    result = generate_text(**arguments)
    available = locales()["locales"]
    language = next(item["label"] for item in available if item["code"] == locale)
    return render(request, "text.html", "text", arguments, data=result, locales=available, language=language,
        previous_url=page_url("/text", **{**arguments, "position": position - 1}) if position > 1 else None,
        next_url=page_url("/text", **{**arguments, "position": position + 1}) if position < 1_000_000 else None)


CSV_COLUMNS = ("position", "full_name", "address", "latitude", "longitude", "height_cm", "weight_kg", "eye_color", "phone", "email")


def csv_cell(value):
    # Numeric coordinates remain numeric. Protect strings opened in spreadsheets.
    if isinstance(value, str) and (value.startswith(("\t", "\r", "\n")) or value.lstrip().startswith(("=", "+", "-", "@"))):
        return "'" + value
    return value


@router.get("/export.csv")
def export_csv(locale: Locale = "en_US", seed: Seed = "42", batch: Batch = 0, batch_size: BatchSize = 10):
    result = users(locale, seed, batch, batch_size)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(CSV_COLUMNS)
    writer.writerows([csv_cell(person[key]) for key in CSV_COLUMNS] for person in result["users"])
    # Filename uses validated locale and integer batch only, never arbitrary seed text.
    filename = f"batchlab-{result['locale']}-batch-{batch + 1}.csv"
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"})


def report_path():
    configured_directory = os.getenv("BENCHMARK_REPORT_DIR")
    if configured_directory:
        return Path(configured_directory) / "benchmark.json"
    local_report = Path("reports") / "benchmark.json"
    if local_report.is_file():
        return local_report
    # This file stays inside the backend bundle when Vercel deploys backend/.
    return Path(__file__).resolve().parent / "static" / "benchmark.json"


@router.get("/benchmark", response_class=HTMLResponse)
def benchmark_page(request: Request):
    path = report_path()
    report = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    return render(request, "benchmark.html", "benchmark", report=report)


@router.get("/benchmark.json")
def benchmark_download():
    path = report_path()
    if not path.is_file():
        raise HTTPException(404, "No benchmark has been recorded.")
    return FileResponse(path, media_type="application/json", filename="benchmark.json", headers={"Cache-Control": "no-store"})


def error_page(request, message, status_code):
    view = "text" if request.url.path == "/text" else "contacts"
    return render(request, "error.html", view, status_code=status_code, message=message, retry_url=str(request.url))
