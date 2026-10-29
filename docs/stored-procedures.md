# PostgreSQL stored procedure reference

The database is the complete fake-data generator. FastAPI validates requests, calls PostgreSQL with bound parameters, and renders the primary Jinja2 HTML interface, CSV exports, and JSON API. Neither application generates a name, random number, address, coordinate, body measurement, phone, or email.

Initialize a UTF-8 PostgreSQL 17 database in this order:

1. `database/001_schema.sql`
2. `database/002_lookup_data.sql`
3. `database/003_procedures.sql`
4. `database/004_markov.sql`
5. `database/005_benchmark.sql`

The generator needs built-in PL/pgSQL and PostgreSQL functions only. It defines **17 stored procedures**: 13 for contacts, 3 for Markov text, and 1 benchmark, with no custom SQL functions or required extensions. [PostgreSQL's CALL documentation](https://www.postgresql.org/docs/17/sql-call.html) describes how output parameters are returned as a row. Generation procedures use an `INOUT p_result` parameter, defaulting to `NULL`; when calling another procedure from PL/pgSQL, pass a local variable in that position. The training procedure updates transition counts instead of returning an output parameter.

## Benchmark procedure

```sql
faker.benchmark_users(p_locale text, p_seed text, p_users integer DEFAULT 10000,
                      p_batch_size integer DEFAULT 100,
                      p_repetitions integer DEFAULT 3,
                      p_warmup_batches integer DEFAULT 5,
                      INOUT p_result jsonb DEFAULT NULL)
```

Runs the real `generate_batch` procedure and measures full generation plus JSON assembly inside PostgreSQL with `clock_timestamp()`. `p_users` is the number per measured run (100–1,000,000, divisible by batch size); batch size is 1–100, repetitions 1–10, warmup batches 0–100. Locale and seed obey the same rules as contact generation. One validation batch and all warmup calls are outside the timer. Counts come from the actual result arrays. The output includes individual runs, measured seconds, actual counts, median users/second, pooled users/second and generator version. It stores no generated users. See [methodology and reproducible examples](benchmark.md).

```sql
CALL faker.benchmark_users('en_US', 'task6-benchmark-v1', 10000, 100, 3, 5, NULL);
```

## Arguments and procedures

The common input arguments are:

| Argument | SQL type | Meaning |
| --- | --- | --- |
| `p_locale` | `text` | A code present in `faker.locales`, initially `en_US` or `de_DE`. |
| `p_seed` | `text` | Exact, case-sensitive seed of 1–64 characters; whitespace-only seeds are rejected. Leading/trailing spaces in a nonempty seed remain significant. |
| `p_position` | `bigint` | Absolute **one-based** person position. Low-level draws permit every positive bigint; complete people are limited to 1–1,000,000. |
| `p_stream` | `text` | A stable, nonempty field label that provides an independent deterministic random stream. |
| `p_result` | varies | Output value passed as `NULL` from plain SQL, or a variable inside PL/pgSQL. Every output below has `DEFAULT NULL`. |

Every signature is listed below. `IN` is implicit for input arguments.

```sql
faker.rng(p_locale text, p_seed text, p_position bigint, p_stream text,
          INOUT p_result bigint DEFAULT NULL)

faker.uniform(p_locale text, p_seed text, p_position bigint, p_stream text,
              INOUT p_result double precision DEFAULT NULL)

faker.uniform_integer(p_locale text, p_seed text, p_position bigint,
                      p_stream text, p_min integer, p_max integer,
                      INOUT p_result integer DEFAULT NULL)

faker.normal(p_locale text, p_seed text, p_position bigint, p_stream text,
             p_mean double precision, p_stddev double precision,
             INOUT p_result double precision DEFAULT NULL)

faker.choose_value(p_locale text, p_seed text, p_position bigint,
                   p_stream text, p_kind text,
                   INOUT p_result text DEFAULT NULL)

faker.generate_globe(p_locale text, p_seed text, p_position bigint,
                     INOUT p_result jsonb DEFAULT NULL)

faker.generate_name(p_locale text, p_seed text, p_position bigint,
                    INOUT p_result jsonb DEFAULT NULL)

faker.generate_address(p_locale text, p_seed text, p_position bigint,
                       INOUT p_result jsonb DEFAULT NULL)

faker.generate_phone(p_locale text, p_seed text, p_position bigint,
                     p_calling_code text,
                     INOUT p_result text DEFAULT NULL)

faker.generate_email(p_locale text, p_seed text, p_position bigint,
                     p_first_name text, p_last_name text,
                     INOUT p_result text DEFAULT NULL)

faker.generate_person(p_locale text, p_seed text, p_position bigint,
                      INOUT p_result jsonb DEFAULT NULL)

faker.list_locales(INOUT p_result jsonb DEFAULT NULL)

faker.generate_batch(p_locale text, p_seed text, p_batch integer,
                     p_batch_size integer,
                     INOUT p_result jsonb DEFAULT NULL)
```

| Procedure | Additional arguments and output |
| --- | --- |
| `rng` | Returns a deterministic integer from 0 through 2⁵²−1. It seeds no session-wide state. |
| `uniform` | Returns a double strictly inside `(0,1)`. |
| `uniform_integer` | `p_min`/`p_max` are inclusive integer endpoints, with `p_min <= p_max`. Returns a uniform discrete selection, subject to the 52-bit generator's negligible discretization error. |
| `normal` | `p_mean` and strictly positive `p_stddev` must be finite. Returns one unrounded Box–Muller normal draw. |
| `choose_value` | `p_kind` selects a lookup dictionary such as `first_name`, `last_name`, or `eye_color`. Returns one entry with equal probability per entry. |
| `generate_globe` | Returns `{latitude, longitude}` in decimal degrees, rounded to six decimals. |
| `generate_name` | Returns `{first_name, middle_name, last_name, title, full_name}`. Empty optional components are empty strings. |
| `generate_address` | Returns `{address, city, region, postal_code, calling_code, street, house_number}`. City metadata stays together. |
| `generate_phone` | `p_calling_code` is the digit-only city area code from `generate_address`, without the national trunk prefix. Returns a localized formatted number. |
| `generate_email` | `p_first_name`/`p_last_name` normally come from `generate_name`. Returns a transliterated ASCII address under a reserved example domain. |
| `generate_person` | Composes the previous procedures into the public person object. Height and weight are rounded to two decimals. |
| `list_locales` | Returns `{locales:[{code,label,country},...]}`. |
| `generate_batch` | `p_batch` is zero-based and nonnegative; `p_batch_size` is 1–100. Returns the complete API payload. Batches beginning after person 1,000,000 are rejected; the final batch can be partial. |

Examples covering every procedure:

```sql
CALL faker.rng('en_US', '42', 1, 'demo', NULL);
CALL faker.uniform('en_US', '42', 1, 'demo', NULL);
CALL faker.uniform_integer('en_US', '42', 1, 'dice', 1, 6, NULL);
CALL faker.normal('en_US', '42', 1, 'body.height', 172, 10, NULL);
CALL faker.choose_value('de_DE', '42', 1, 'demo.first', 'first_name', NULL);
CALL faker.generate_globe('en_US', '42', 1, NULL);
CALL faker.generate_name('de_DE', '42', 1, NULL);
CALL faker.generate_address('de_DE', '42', 1, NULL);
CALL faker.generate_phone('de_DE', '42', 1, '30', NULL);
CALL faker.generate_email('de_DE', '42', 1, 'Jürgen', 'Müller', NULL);
CALL faker.generate_person('en_US', '42', 1, NULL);
CALL faker.list_locales(NULL);
CALL faker.generate_batch('en_US', '42', 0, 20, NULL);
```

For procedural composition:

```sql
DO $$
DECLARE payload jsonb;
BEGIN
    CALL faker.generate_batch('de_DE', 'an arbitrary seed', 2, 10, payload);
    RAISE NOTICE 'First position: %', payload->'users'->0->>'position'; -- 21
END;
$$;
```

## Randomness and reproducibility

The v1 counter key is PostgreSQL's textual serialization of this JSONB array:

```text
["sql-faker-v1", locale, seed, absolute_position, stream_label]
```

`rng` takes the first 13 hex digits of built-in `md5(key)`, interprets them as an unsigned 52-bit integer `x`, and `uniform` returns `(x + 0.5) / 2^52`. The explicit JSON tuple prevents collisions from ambiguous string concatenation, including seeds containing separators, quotation marks, or Unicode. MD5 serves as a deterministic pseudorandom mixer; this generator is unsuitable for cryptographic secrets.

Each field uses its own descriptive label: `name.first`, `name.last`, `address.city`, `body.height.u`, `body.weight.v`, `globe.latitude`, and so on. Optional title/middle components have independent selection streams. There is no `random()`, `setseed()`, mutable counter, generated-person table, dependence on the current time, or application-level fake-data library.

For batch `b`, size `s`, and one-based index `i` inside the batch:

```text
position = b * s + i
```

Consequently, person 21 is identical in batch 2 of size 10, batch 1 of size 20, and a direct call with position 21. Repeating calls, restarting the API, changing connections, concurrent requests, and visiting batches in a different order produce the same data. The API preserves seeds as strings, including leading zeros, rather than coercing them into integers.

The reproducibility contract assumes the same versioned SQL, lookup content/order, locale metadata, and PostgreSQL runtime. The target container pins PostgreSQL major version 17. Cross-major or cross-platform floating-point identity is not guaranteed; transcendental math can differ slightly across runtimes. Changing a dictionary or template can remap choices, so freeze v1 data or make an explicit versioned migration. Re-running the initialization files does not overwrite existing lookup rows.

## Distributions

`normal` uses Box–Muller with independent uniforms:

```text
z = sqrt(-2 * ln(u)) * cos(2 * pi * v)
result = mean + stddev * z
```

Both locales currently use height **N(172 cm, 10² cm²)** and weight **N(75 kg, 12² kg²)**. They have independent streams and no gender mixture. There is no clipping, rejection, or re-centering, which would distort the requested normal distribution. As with any normal model, mathematical tails can be nonphysical; the probability of a negative weight is about 2×10⁻¹⁰ before finite-generator effects. These are synthetic population parameters, not medical or demographic claims.

Uniform points on a sphere use `latitude = degrees(asin(2*u - 1))` and `longitude = 360*v - 180`. Equal-width bins of `sin(latitude)` and longitude therefore have equal probability. Sampling latitude uniformly would overpopulate the poles. Coordinates intentionally cover the **entire globe**, independently of the address; they are not geocoded city coordinates.

Names use optional titles at 10%, middle names at 35%, and a second surname at 8% (an identical second surname is omitted). Lookup entries, city choices, address/phone layouts, and eye colors use uniform selection. These vocabulary choices emphasize variation and are not intended to reproduce census frequencies.

## Lookup data and locale extension

Every locale lives in the same tables: `faker.locales` holds metadata and normal parameters; `faker.lookup_sets(locale,kind,entries)` holds ordered arrays; `faker.cities(locale,ordinal,name,region,postal_code,calling_code)` pairs factual city metadata. The relational view `faker.lookup_values(locale,kind,ordinal,value)` makes dictionaries easy to inspect. No per-locale tables or locale-specific branches are needed.

| Dictionary | en_US | de_DE |
| --- | ---: | ---: |
| First names | 690 | 2,002 |
| Surnames | 1,000 | 1,400 |
| Street stems | 163 | 172 |
| Street suffixes | 10 | 4 |
| Titles | 4 | 4 |
| Eye colors | 6 | 6 |
| Address layouts | 3 | 3 |
| Phone layouts | 3 | 3 |
| Cities with postal/phone metadata | 62 | 72 |

Name data is bundled from MIT-licensed Faker 37.12.0 provider dictionaries; see [database/NOTICE.md](../database/NOTICE.md) and the preserved license. German surnames combine three German-language providers. Street stems/templates/city facts are authored static data. The optional exporter reads dictionaries only; it does not generate user records. Faker is not a runtime dependency.

US layouts place the house number before the street and use city/state/ZIP; variants add `Apt.` or `Unit`. German layouts place the house number after the street and postcode before the city; variants add `Whg.` or a house-letter suffix. Both use a city-associated telephone area code and one of three layouts with `+1` or `+49`. Generated addresses are plausible synthetic combinations, not deliverable-address validation. Generated phone numbers are synthetic and are not guaranteed to be non-routable.

Emails explicitly transliterate German `ä/ö/ü/ß` into `ae/oe/ue/ss`, map a broad Latin accent set, remove unsupported characters, and lowercase ASCII using the `C` collation. The first/last components are length-bounded and the absolute position is appended, keeping the local part under 64 characters and ensuring uniqueness within a locale/seed dataset. Domains are `example.com`, `example.org`, and `example.net`, which [IANA reserves for documentation](https://www.iana.org/help/example-domains).

To add a locale, insert its metadata, contiguous or noncontiguous positive city ordinals, and all eight lookup kinds above. Templates support `{number}`, `{street}`, `{city}`, `{region}`, `{postal}`, `{unit}` for addresses; `{stem}`/`{suffix}` for streets; and `{area}`/`{subscriber4}`/`{subscriber7}` for phones. Extend transliteration or template token support deliberately when a new writing system or numbering plan needs it. `list_locales` makes new locales available to the API automatically.

## Markov text procedures

`004_markov.sql` adds original English and German training corpora to `faker.text_corpora(locale,model_version,corpus,attribution)`. The same shared tables support every locale. Each corpus line is one complete sentence; no external download, Python training, Lorem ipsum, or runtime text-generation library is used.

```sql
faker.train_markov(p_locale text, p_model_version text DEFAULT 'sql-markov-v1')

faker.markov_next(p_locale text, p_seed text, p_position bigint, p_step integer,
                  p_previous_first text, p_previous_second text, p_model_version text,
                  INOUT p_result text DEFAULT NULL)

faker.generate_text(p_locale text, p_seed text, p_position bigint, p_word_count integer,
                    INOUT p_result jsonb DEFAULT NULL)
```

| Procedure | Arguments, algorithm, and result |
| --- | --- |
| `train_markov` | Reads the exact locale/version corpus and splits each line into whitespace-separated word tokens. Attached punctuation and German capitalization are preserved. Counts every `(previous word 1, previous word 2, next word)` triple in `faker.markov_transitions`; `weight` is the observed count. The two-word initial context is `('<s>','<s>')`. Replaces only that locale/version's trained transitions. Call after adding or deliberately updating a corpus. |
| `markov_next` | `p_step` is a positive word index. The two previous tokens and model version identify a state. Uses `faker.uniform` with stream `text.<model version>.word.<step>` and selects a successor from cumulative observation weights, ordered using `COLLATE "C"`. A successor observed 9 times has 9 times the probability of one observed once. Returns the selected token, and rejects a missing state. |
| `generate_text` | `p_position` identifies sample 1–1,000,000; `p_word_count` is an exact count of 10–500 whitespace-separated tokens. Locale and seed use the same validation as contact generation. Walks the second-order chain, resets to the initial context after `.`, `!`, or `?`, and adds a final full stop if the requested length cuts off a sentence. Returns `{locale,seed,position,word_count,text,model_version,chain_order:2}`. The model version is currently `sql-markov-v1`. |

```sql
CALL faker.train_markov('en_US');
CALL faker.train_markov('de_DE');
CALL faker.markov_next('de_DE','42',1,1,'<s>','<s>','sql-markov-v1',NULL);
CALL faker.generate_text('en_US','42',1,80,NULL);
CALL faker.generate_text('de_DE','42',1,80,NULL);
CALL faker.generate_text('de_DE','42',2,80,NULL); -- next independent sample
```

This is a **second-order word-level Markov chain**: the next-word distribution depends on the preceding two words. Shared contexts branch into different successors, recombining patterns instead of choosing from a list of whole passages. It models local language patterns and does not guarantee semantic or grammatical coherence. Repeated phrases are possible.

The random key includes the exact locale, seed, sample position, model version and word index through the shared versioned RNG. Identical arguments reproduce the same text with the same SQL, corpora and runtime. Increasing the requested length preserves the existing word sequence, except that the shorter result may have received a final full stop. Text calls use independent stream labels and do not change any contact. Freeze the corpus and transition ordering for a published model version; use an explicit new version for future vocabulary changes.

`GET /api/text?locale=de_DE&seed=42&position=1&word_count=80` binds these arguments to `generate_text`. Defaults are English, seed `42`, sample 1, and 80 words. FastAPI validates and returns the stored procedure payload. The primary Python-rendered `/text` page supports language, seed, word count, previous/next sample, and copying the result. Its pagination follows the applied arguments until Generate resets the sample to 1.

For an existing database, apply `004_markov.sql` once before rebuilding the API and frontend. It is safe to reapply: existing versioned corpora are preserved and their transition counts are rebuilt deterministically. To extend a new locale, add its metadata and corpus, then call `train_markov` before generating text.

## Contact API boundary and verification

`GET /api/users` binds locale, seed, batch, and batch size into `CALL faker.generate_batch(%s,%s,%s,%s,NULL)`. SQLSTATE `22023` maps to HTTP 422; database connection/query failures map to HTTP 503 without exposing connection strings. `GET /api/locales` calls `list_locales`; `GET /api/health` probes the initialized database. The FastAPI root renders an escaped HTML table using the same procedure payload and a GET form with previous/next links.

The batch payload has `locale`, `seed` (string), `batch`, `batch_size`, `total` (1,000,000), `has_next`, and `users`. Each user has `position`, `full_name`, `address`, `latitude`, `longitude`, `height_cm`, `weight_kg`, `eye_color`, `phone`, and `email`.

Run the checked-in SQL smoke script with `psql -v ON_ERROR_STOP=1 -f database/smoke_checks.sql`. It checks repeated-call identity, page-size partition equivalence, position numbering, locale influence, uniform endpoints, coordinate/email shape, and the final partial batch. Backend validation/outage checks are in `backend/tests`; the broader API/SQL/distribution acceptance suite is in `tests/`.
