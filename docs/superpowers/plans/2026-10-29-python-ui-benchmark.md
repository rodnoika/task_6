# Primary Python interface and measured SQL throughput

Requested change: serve the existing compact Batchlab design from Python, and record a real users/second benchmark. This replaces the original Next.js runtime requirement. User authorized implementation directly.

1. Preserve current CSS and contact/text structure in FastAPI Jinja2 templates. Use GET forms and server-generated navigation links. Keep all generated values in PostgreSQL; small browser helpers only expand details, choose seed arguments, and copy text.
2. Keep JSON API and flat `/preview` compatible. Escape template values, validate all arguments, protect spreadsheet CSV strings, and render recoverable HTML errors. Remember each generator's applied URL across tab switches.
3. Add a bounded, CALL-able SQL benchmark using `clock_timestamp()`, actual JSON user counts, excluded validation/warmup calls, repeated complete batches, median and pooled throughput. A Python CLI writes raw JSON and a readable report; an HTML benchmark page displays the saved measurements.
4. Replace the old frontend service with Python on the existing 3000 and 8000 host ports, keeping the PostgreSQL volume. Following the user's 2026-10-30 cleanup request, remove the superseded frontend source, dependencies, build artifacts and Dockerfile.
5. Run real database, API and Python HTML acceptance tests; inspect desktop/mobile behavior; run the measured 10,000 users × 3 repeats per locale benchmark and document results.

Verification: HTTP HTML must already contain SQL-generated contacts/text before scripts run. Pagination, locale/seed changes, CSV, tab restoration, final partial batch and errors must work. SQL benchmark tests check true counts and recompute rates from stored seconds. The final report must contain actual execution samples and reproducible commands.
