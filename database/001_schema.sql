-- All generation is implemented by CALL-able PL/pgSQL procedures (003).
CREATE SCHEMA IF NOT EXISTS faker;

CREATE TABLE IF NOT EXISTS faker.locales (
    code text PRIMARY KEY,
    label text NOT NULL,
    country text NOT NULL,
    country_code text NOT NULL,
    address_template text NOT NULL,
    street_template text NOT NULL,
    phone_template text NOT NULL,
    house_number_max integer NOT NULL CHECK (house_number_max > 0),
    height_mean double precision NOT NULL DEFAULT 172,
    height_stddev double precision NOT NULL DEFAULT 10 CHECK (height_stddev > 0),
    weight_mean double precision NOT NULL DEFAULT 75,
    weight_stddev double precision NOT NULL DEFAULT 12 CHECK (weight_stddev > 0),
    generator_version text NOT NULL DEFAULT 'sql-faker-v1'
);

-- One shared schema for every locale; arrays preserve versioned lookup order.
CREATE TABLE IF NOT EXISTS faker.lookup_sets (
    locale text NOT NULL REFERENCES faker.locales(code),
    kind text NOT NULL,
    entries text[] NOT NULL CHECK (cardinality(entries) > 0),
    PRIMARY KEY (locale, kind)
);

-- Convenient relational inspection without duplicating the stored dictionaries.
CREATE OR REPLACE VIEW faker.lookup_values AS
SELECT s.locale, s.kind, v.ordinal, v.value
FROM faker.lookup_sets AS s
CROSS JOIN LATERAL unnest(s.entries) WITH ORDINALITY AS v(value, ordinal);

CREATE TABLE IF NOT EXISTS faker.cities (
    locale text NOT NULL REFERENCES faker.locales(code),
    ordinal integer NOT NULL CHECK (ordinal > 0),
    name text NOT NULL,
    region text NOT NULL,
    postal_code text NOT NULL CHECK (postal_code ~ '^[0-9]{5}$'),
    calling_code text NOT NULL CHECK (calling_code ~ '^[0-9]+$'),
    PRIMARY KEY (locale, ordinal)
);
