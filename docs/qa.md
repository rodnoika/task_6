# Acceptance and QA

## Interface redesign verification

The user requested removal of the generic AI-generated appearance. The interface now uses separate Contacts and Text views, compact parameter bars, readable data rows, and a plain text output field. The visual review and research sources are recorded in `docs/design-review.md`.

The 12 frontend tests, TypeScript check, and Docker production build passed. Live browser checks covered the Text deep link, active navigation, contact pagination/replay, state preserved across views, and desktop/mobile layouts without horizontal overflow. CSV output was parsed independently and all ten fields of all ten records matched the actual API batch. Browser error logs were empty. No database algorithms or API contracts were changed for this redesign.

The acceptance tests exercise the running FastAPI service and PostgreSQL procedures. They do not generate replacement data in Python. Public positions are one-based; batch indices are zero-based.

## Running the checks

Start the application using the repository instructions, then run from the repository root:

```powershell
python -m pip install -r tests/requirements.txt
$env:API_BASE_URL = 'http://localhost:8000'
$env:DATABASE_URL = 'postgresql://faker:faker@localhost:5432/faker'
$env:REQUIRE_LIVE_API = '1'
python -m pytest tests -q -rs
```

An unconfigured API/database is skipped for local test discovery. `REQUIRE_LIVE_API=1` makes an unavailable API a failure; a configured `DATABASE_URL` always requires a working database. A skipped integration test is not a verified acceptance criterion. Network access must be allowed for localhost.

To verify replay across a real restart, preserve a snapshot before restarting services:

```powershell
python tests/replay_snapshot.py save tests/.runtime/restart.json
docker compose restart db api
docker compose ps
# Wait for database and API readiness before checking.
python tests/replay_snapshot.py check tests/.runtime/restart.json
```

The snapshot includes both locales, a Unicode seed with punctuation, an interior batch, and the final partial batch. Save refuses to overwrite an existing snapshot so post-restart output cannot replace the baseline. Restart checks use the same generator version and lookup dataset.

For an isolated outage check, start a second API process on another port with `DATABASE_URL` pointing to a closed port (for example `postgresql://faker:faker@127.0.0.1:1/faker`). Set `OUTAGE_API_BASE_URL` to that process and run `python -m pytest tests/test_outage.py -q`. This checks real connection failures without stopping the healthy application database. `/api/users`, `/api/locales`, and `/api/health` must return 503 rather than replacement data.

## Acceptance coverage

| Behavior | Check |
| --- | --- |
| Locale discovery | Both `en_US` and `de_DE` include labels and country metadata |
| Required generated fields | Nonempty localized strings, finite numeric values, bounded coordinates, plausible physical values in the sample, valid email shape |
| Python HTML requirement | Actual preview table includes all ten SQL fields for both locales; a script-shaped seed is escaped |
| Pagination | First/next are contiguous, page-size changes preserve absolute positions, final partial batch reaches position 1,000,000 |
| Invalid requests | Unsupported locale, empty/long seed, noninteger/negative batch, out-of-range batch, invalid size return 422 |
| Determinism | Repeat requests, mixed seeds/locales, request interleaving, concurrent requests, new database sessions, actual restart snapshot |
| Localization and variety | Correct country phone prefixes and postal shapes; names, addresses, phone numbers, emails and eye colors vary |
| Distribution | Fixed-seed normal moments/bin frequencies and equal-area sphere bins; generated records come from SQL |
| Architecture | PostgreSQL generation routines are stored procedures, lookup datasets have meaningful cardinality, API returns procedure output |

## Execution record

On 2026-10-29, all **47 acceptance cases passed across the healthy and outage configurations**:

- Healthy API/native SQL: **44 passed, 3 outage cases skipped in 27.87 seconds**, using native PostgreSQL **18.6** on `127.0.0.1:55432` and FastAPI on `127.0.0.1:8006`.
- Isolated API configured with an unavailable database: **3 passed in 9.26 seconds**, using `OUTAGE_API_BASE_URL=http://127.0.0.1:8007`. Users, locales and health returned 503 without replacement records or a connection URL in the response.

`REQUIRE_LIVE_API=1` was enabled for the healthy run; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` excluded unrelated globally installed pytest plugins. The API, direct SQL, lookup capacity, concurrent/session replay, HTML preview, millionth-position boundary, distribution and outage cases all executed.

| Locale | Height mean / sample SD (cm) | Weight mean / sample SD (kg) | Sphere z-bin χ² | Longitude-bin χ² |
| --- | --- | --- | --- | --- |
| en_US | 172.0800 / 10.1326 | 74.8842 / 12.0478 | 5.544 | 6.044 |
| de_DE | 172.2199 / 10.0338 | 75.1232 / 11.9481 | 9.936 | 6.860 |

Both locales passed all moment, normal-bin, equal-area sphere and independence thresholds. The million-person check exercised direct access to the final partial batch and position 1,000,000; it did not eagerly generate one million rows or claim million-row throughput.

The distribution suite generates 5,000 records per locale (10,000 total), with fixed seed `qa-distribution-v1`. It checks height N(172, 10) and weight N(75, 12), with mean tolerance 0.08 standard deviations, standard deviation tolerance 7%, and six normal bins at −2, −1, 0, 1, 2 standard deviations. These are untruncated normals rounded to two decimals; the checks do not assert hard physical bounds for every theoretical tail. Sphere checks use ten equal bins of `sin(latitude)` and longitude, second moments and coordinate independence. Uniform latitude fails the equal-area test. Separate correlation checks catch accidentally shared height/weight streams.

The Docker target uses PostgreSQL 17, which has not been executed by this QA run. The Compose configuration validates successfully, but Docker's Linux engine was unavailable. The native integration environment used PostgreSQL 18.6.

### Final integration verification

The integration owner independently reran the complete suite after final SQL installation and a real database restart:

```powershell
$env:API_BASE_URL = 'http://127.0.0.1:8006'
$env:DATABASE_URL = 'postgresql://faker:faker@127.0.0.1:55432/faker'
$env:OUTAGE_API_BASE_URL = 'http://127.0.0.1:8007'
$env:REQUIRE_LIVE_API = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest backend/tests tests -q
```

Result: **57 passed in 48.91 seconds**, no skips. This includes 10 backend unit checks and the original 47 acceptance checks. Final handoff review added one further regression for omitted API arguments: it exposed a 20-person default inconsistent with the documented 10-person default. Both the API and Python preview defaults were corrected to 10 and verified separately; this brings the acceptance suite to 48 cases. The frontend's **9 tests passed**, its TypeScript check passed, and its Next.js production build passed. The active frontend was rebuilt with `API_INTERNAL_URL=http://127.0.0.1:8006` and serves on port 3006 to avoid other projects on ports 3000/8000.

An actual PostgreSQL stop/start using the isolated project's data directory reproduced **37 records across 3 saved cases exactly**, including both locales, a Unicode seed, an interior batch and a final partial batch. Reapplying the final initialization SQL and the stored procedure smoke checks also succeeded.

After correcting the defaults, the new regression plus the 10 backend checks passed together: **11 passed in 9.07 seconds**. The Python-rendered root page independently returned exactly 10 contacts with no query arguments. Across the final verification runs, all **67 distinct automated checks** passed (58 backend/acceptance and 9 frontend).

Live browser checks at **1440 × 1000** and **390 × 844** verified responsive layout and contact detail visibility. At mobile width, the document had no horizontal overflow. Editing locale and seed before clicking Next continued the applied US/42 dataset; Generate then applied the edited German seed and reset to batch 1. Next followed by Previous restored the displayed records exactly. Browser error logs were empty.

The browser successfully downloaded CSV; an independent parser compared **all 10 fields of all 10 exported records** with the actual SQL-backed API batch. Screenshots were saved locally in `.runtime/desktop.png` and `.runtime/mobile.png`. The temporary outage API is stopped after verification; the application preview uses frontend 3006, API 8006 and database 55432.

## Source review

The SQL source uses JSON-array encoding for version, locale, seed, position and field labels, avoiding ambiguous concatenation. Its 52-bit uniform transformation stays in the open interval; normal attributes use separate Box–Muller streams, and globe generation transforms a uniform sample through `asin(2u−1)`. Generation is implemented in procedures and calls PostgreSQL built-ins rather than a Python/JavaScript fake-data library.

The initial address and phone implementation applied a single template per locale. QA flagged the lack of formatting variety, and the data/procedure implementation now selects from three shared address formats and three phone formats per locale. API checks exercise phone punctuation variety and name-layout variety; SQL checks verify available format dictionaries. The frontend state source preserves the successful query for displayed records so draft edits or a failed request cannot silently change pagination arguments.

The live SQL/API checks above verified these observations against the running application.

## Markov text addition

The application now includes English and German text generation with a second-order, word-level Markov chain. `004_markov.sql` stores original corpora and trains frequency-weighted transitions entirely in SQL. Three new procedures handle training, weighted next-token selection and deterministic passage generation; contact fields and their RNG streams are unchanged.

On the Docker PostgreSQL 17.11 environment, `python -m pytest backend/tests tests -q` completed with **72 passed, 3 skipped in 70.50 seconds**. The three skips are the optional standalone outage API checks; their separate test server was stopped. The backend's real closed-port outage unit test also covers the text endpoint. The frontend completed **12 tests**, TypeScript checking and a Docker production build successfully.

The 17 Markov acceptance checks cover both languages; exact lengths and punctuation; repeated requests and changed seed/sample; invalid inputs; direct SQL/API equality; independent reference counts for the training corpora; generated tokens following actual trained transitions; prefix stability across word counts; a controlled 9:1 weighted-draw distribution; and preservation of the contact sequence after a 500-word text request.

The final backend unit rerun also passed **10 tests in 69.37 seconds**, including the newly extended check that `/api/text` returns HTTP 503 and no generated fallback when its database connection fails.

Live browser checks verified generating English and German text, copying the result, changed samples, and exact previous-sample replay. Changing draft language before Next preserved the language of the displayed sample until Generate applied the new settings. Layout was checked at 1280 × 900 and 390 × 844; mobile content stayed within the viewport, and browser error logs were empty. Screenshots are saved in `.runtime/markov-desktop.png` and `.runtime/markov-mobile.png`. The current Docker database was migrated in place and API/web images rebuilt; no volume reset is required.

## Docker startup follow-up

Windows rejected a host bind on port 5432 with error 10013. A direct bind check confirmed 55436 was available. The default Compose database host port and `.env.example` now use 55436; container-to-container PostgreSQL connections remain on `db:5432`.

After `docker compose up -d`, PostgreSQL **17.11** and the API were healthy, and the web container was running. The database initialization executed the SQL smoke checks successfully (`DO`). HTTP verification confirmed API database readiness, the Batchlab page on port 3000, and ten German contacts returned through the Next.js API proxy. The full statistical suite above was run on native PostgreSQL 18.6; this follow-up verifies actual Docker 17 initialization and end-to-end connectivity.

## Primary Python interface and real benchmark — 2026-10-30

The main application on port 3000 now renders HTML through FastAPI/Jinja2. Port 8000 exposes the same application. Compose runs only `db` and `api`; the superseded Next.js container was removed without deleting the PostgreSQL volume. Contact and Markov SQL algorithms and deterministic streams were preserved.

The full Python/API/SQL run on Docker PostgreSQL **17.11** completed with **96 passed, 3 skipped in 63.83 seconds**. The three skipped checks require a separately configured outage API process; the regular unit suite independently exercised a real closed database port, including HTML outage pages. Coverage included direct SQL benchmark counts/timings and invalid arguments, normal and sphere distributions, reproducibility, HTML escaping, CSV formula protection, real SQL values in the primary HTML, pagination, and per-generator remembered arguments.

After the final current-tab navigation fix and addition of the saved benchmark-page check, the focused acceptance run against the final service completed with **8 passed in 2.14 seconds**:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:REQUIRE_LIVE_API='1'
$env:API_BASE_URL='http://127.0.0.1:3000'
python -m pytest tests/test_python_ui.py -q
```

Live browser checks confirmed German contact generation through the HTML form, next/previous batches and exact replay, row expansion, German Markov generation, different next samples, exact previous-sample replay, copying, and remembered contact arguments when returning from Text. Desktop and mobile layouts retained the compact design. A 320px viewport check after the narrow-screen navigation adjustment showed document width equal to client width (305px after the browser scrollbar), with no horizontal page overflow. Browser warning/error logs were empty. Screenshots are saved under `.runtime/python-*.png`, including the final `/benchmark` page.

The actual benchmark ran after the full test workload, using three measured runs of **10,000 complete users per locale**, batch size 100, one excluded validation batch, and five excluded warmup batches. All 60,000 measured users were generated by the real SQL procedures. Median throughput was **223.55 users/second for en_US** and **191.49 users/second for de_DE**. Pooled throughput was **177.56** and **192.61 users/second**, respectively. One English run was slower (80.21s versus about 44s); every raw sample is retained rather than discarded. Hardware/load affects timing.

The [raw JSON](../reports/benchmark.json), [readable report](../reports/benchmark.md), and [methodology](benchmark.md) document actual seconds, counts, median/pooled rates, versions and reproducible commands. The `/benchmark` page displays this saved report and offers its real JSON file. Rebuilding/restarting the Python container preserved the report through the `reports/` mount. Both final Compose services were healthy; the isolated QA container was removed.

## Remove superseded frontend — 2026-10-30

At the user's explicit request, deleted the entire legacy frontend directory, including source, TypeScript tests/configuration, package manifests, node_modules, and build artifacts. Removed docker/web.Dockerfile and obsolete ignore rules. Updated active setup/design documents to point to the Python HTML templates. Earlier entries above remain a chronological record of the replaced implementation.

Fresh HTTP checks confirmed `/`, `/text`, and `/benchmark` each return HTTP 200 and `text/html` from Uvicorn, contain the Python static stylesheet, and have no Next asset references. After deletion, the focused real-service HTML/CSV/navigation/benchmark suite completed with **8 passed in 1.81 seconds**. Compose configuration lists exactly `db` and `api`. A filesystem scan found no frontend directory, Node package manifests, Next configuration, or TSX files in the active project.

## Full assignment compliance audit — 2026-10-30

Reviewed the complete current Python/HTML application, stored procedures, schema/reference data, Markov implementation, documentation, benchmark samples and submission requirements.

Fresh full verification on the running application and Docker PostgreSQL 17.11: **100 passed in 79.25 seconds, zero skips**. This run configured a separate temporary outage API on loopback port 8007, so all three previously optional real-service outage scenarios ran successfully. The main database was never stopped. The test-only outage container was stopped after verification.

A second check created a new temporary database, installed all five ordered SQL files plus smoke_checks.sql, confirmed that all 17 custom routines are procedures, generated ten contacts and 80 Markov words in each locale, and executed a measured 100-user benchmark. The newly created audit database was then deleted; the working database and saved benchmark were preserved.

Live reference counts matched the documentation: en_US has 690 first names, 1,000 surnames, 163 street stems and 62 cities; de_DE has 2,002 first names, 1,400 surnames, 172 street stems and 72 cities. The shared locale-keyed schema, one-million-position boundary, optional name/address/phone formats, Box–Muller normal draws, equal-area sphere sampling and deterministic field streams satisfy the functional task. Python renders HTML and reads CALL results; the runtime contains no application-level fake contact generator or Next.js code. Optional Markov generation is implemented entirely in SQL with frequency-weighted second-order transitions.

Checked the saved benchmark arithmetic independently: each locale contains three real 10,000-user samples; total counts, median rates and pooled rates recompute from the raw seconds. The stored procedure reference covers signatures and invocation examples for all 17 procedures.

No assignment-blocking implementation issue was found in this audit. Submission items still requiring preparation beyond application hosting: provide a recorded video demonstration, publish/share an accessible link to the stored-procedure documentation, state the author's full name, and assemble the submission email with the video, documentation/application links and existing benchmark result. No video file, public documentation URL or author full name was found in the current project. These items may exist elsewhere and should be supplied by the author.
