# Task 6 DATA design

Build a local application with Python (FastAPI + Jinja2) and PostgreSQL 17. This specification reflects the user's Python interface migration and 2026-10-30 removal of the superseded frontend. The assignment supplies the functional scope.

## Ownership and data flow

The browser submits locale, seed, batch, and batch size through HTML GET forms to FastAPI. Python validates the arguments, calls `faker.generate_batch`, and renders the returned data in Jinja2 HTML templates. PostgreSQL alone generates every fake contact field.

The database stores shared locale-aware reference tables, rather than a table per language. It supports `en_US` and `de_DE` and at most 1,000,000 addressable positions per locale and seed. This is a deterministic sequence, not a promise that every randomly assembled name is unique.

## Contract

`GET /api/locales` returns `{locales: [{code, label, country}]}`. `GET /api/users?locale=en_US&seed=42&batch=0&batch_size=10` returns `{locale, seed, batch, batch_size, total: 1000000, has_next, users}`. The seed is a nonempty string of at most 64 characters; batch is zero-based; batch size is 1–100. Public record positions are one-based. A final partial batch is valid; a batch starting beyond the sequence is invalid.

Each user contains `position`, `full_name`, `address`, `latitude`, `longitude`, `height_cm`, `weight_kg`, `eye_color`, `phone`, and `email`. Bad input returns HTTP 422 and an unavailable database returns HTTP 503. `/api/health` reports database readiness. The primary contact, text and benchmark pages are Python-rendered HTML; the same service also exposes the JSON API.

## Algorithms

Use stateless hash-derived open-interval uniform samples, with unambiguous input encoding and independent labels for fields. The random key includes generator version, locale, seed, and absolute one-based position `batch * batch_size + index + 1`, where index is zero-based. This makes direct access, interleaving, and page-size changes reproducible. Use Box–Muller for normal physical attributes and `latitude = asin(2u - 1)`, `longitude = 2πv - π` for equal-area points on the entire sphere. Coordinates are independent of the localized postal address.

Names vary titles and middle names; addresses and telephone numbers vary locale-appropriate formatting. Static bundled lookup data has source attribution. Email uses reserved example domains. Versioned lookup data is part of the reproducibility contract.

## Interface

Compact neutral background, dark typography, restrained blue accents, generator controls, and a readable contact table with expandable details. On smaller screens the layout adapts without hiding required data. The interface distinguishes draft arguments from applied arguments, resets to the first batch on generation, supports next/previous, exports the applied SQL batch as CSV, and provides accessible error feedback.

## Verification

Run Python unit tests, live HTML/API checks, and direct SQL acceptance tests. Test repeated and interleaved calls, locale and seed changes, position bounds, lookup capacity, format variation, and distributions with deterministic samples. Inspect the live UI at desktop and mobile widths. Docker Compose runs the database and Python application; native development instructions use the same SQL and HTML templates.

