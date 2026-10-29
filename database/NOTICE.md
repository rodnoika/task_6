# Static dictionary sources

The name dictionaries in `002_lookup_data.sql` are a development-time extraction from **Faker 37.12.0**, released under the MIT license. Its full copyright and permission notice is preserved in [vendor/Faker-LICENSE.txt](vendor/Faker-LICENSE.txt). No Faker generator is instantiated by the exporter. Python Faker is absent from the application dependencies, and no Python generation runs when serving requests or initializing PostgreSQL.

Upstream source: [joke2k/faker, tag v37.12.0](https://github.com/joke2k/faker/tree/v37.12.0).

- US first/surnames: [`faker/providers/person/en_US`](https://github.com/joke2k/faker/tree/v37.12.0/faker/providers/person/en_US).
- German first names: [`faker/providers/person/de_DE`](https://github.com/joke2k/faker/tree/v37.12.0/faker/providers/person/de_DE).
- German-language surnames: ordered union of [`de_DE`](https://github.com/joke2k/faker/tree/v37.12.0/faker/providers/person/de_DE), [`de_AT`](https://github.com/joke2k/faker/tree/v37.12.0/faker/providers/person/de_AT), and [`de_CH`](https://github.com/joke2k/faker/tree/v37.12.0/faker/providers/person/de_CH). This includes surnames shared across German-speaking countries and increases variation beyond the small German provider alone. Ordering and exact spellings are frozen in the SQL file; duplicate literals are removed while preserving first occurrence.

The common street stems, street suffixes, honorific lists, eye colors, address/phone templates, and city metadata are authored in `build_lookup_data.py` for this project. City names, regional abbreviations, central postal codes, and telephone calling codes are factual geographic metadata; each city is paired with one representative central postal code, not its full postal-code coverage. Streets and house numbers are synthetic combinations and are not an actual street directory.

To regenerate the checked-in static SQL:

```powershell
python -m pip download --no-deps --dest database/vendor Faker==37.12.0
python database/build_lookup_data.py
```

The wheel is a development input and is not included in the application or database image. Re-exporting a different Faker version changes the lookup vocabulary and can change generated people. Keep this SQL frozen for v1, or introduce a new generator/data version deliberately.
