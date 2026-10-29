-- Generator v1: no user-defined functions, extension, random(), or session RNG state.
CREATE OR REPLACE PROCEDURE faker.rng(
    p_locale text, p_seed text, p_position bigint, p_stream text,
    INOUT p_result bigint DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    version text;
BEGIN
    SELECT generator_version INTO version FROM faker.locales WHERE code = p_locale;
    IF version IS NULL OR p_seed IS NULL OR length(p_seed) NOT BETWEEN 1 AND 64
       OR p_seed ~ '^[[:space:]]*$' OR p_position IS NULL OR p_position < 1
       OR p_stream IS NULL OR p_stream = '' THEN
        RAISE EXCEPTION 'Invalid locale, seed, position, or stream' USING ERRCODE = '22023';
    END IF;
    -- JSON arrays distinguish ambiguous tuples, including separators inside seeds.
    p_result := ('x' || substr(md5(jsonb_build_array(
        version, p_locale, p_seed, p_position, p_stream
    )::text), 1, 13))::bit(52)::bigint;
END;
$$;

CREATE OR REPLACE PROCEDURE faker.uniform(
    p_locale text, p_seed text, p_position bigint, p_stream text,
    INOUT p_result double precision DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    state bigint;
BEGIN
    CALL faker.rng(p_locale, p_seed, p_position, p_stream, state);
    -- Open (0,1), so logarithms and inverse transforms never see endpoints.
    p_result := (state::double precision + 0.5) / 4503599627370496.0;
END;
$$;

CREATE OR REPLACE PROCEDURE faker.uniform_integer(
    p_locale text, p_seed text, p_position bigint, p_stream text,
    p_min integer, p_max integer, INOUT p_result integer DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    u double precision;
BEGIN
    IF p_min IS NULL OR p_max IS NULL OR p_max < p_min THEN
        RAISE EXCEPTION 'Invalid inclusive integer interval' USING ERRCODE = '22023';
    END IF;
    CALL faker.uniform(p_locale, p_seed, p_position, p_stream, u);
    p_result := p_min + floor(u * (p_max::bigint - p_min::bigint + 1))::bigint;
END;
$$;

CREATE OR REPLACE PROCEDURE faker.normal(
    p_locale text, p_seed text, p_position bigint, p_stream text,
    p_mean double precision, p_stddev double precision,
    INOUT p_result double precision DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    u double precision;
    v double precision;
BEGIN
    IF p_mean IS NULL OR p_stddev IS NULL OR p_stddev <= 0
       OR p_mean::text IN ('NaN', 'Infinity', '-Infinity')
       OR p_stddev::text IN ('NaN', 'Infinity', '-Infinity') THEN
        RAISE EXCEPTION 'Normal parameters must be finite with positive deviation' USING ERRCODE = '22023';
    END IF;
    CALL faker.uniform(p_locale, p_seed, p_position, p_stream || '.u', u);
    CALL faker.uniform(p_locale, p_seed, p_position, p_stream || '.v', v);
    p_result := p_mean + p_stddev * sqrt(-2 * ln(u)) * cos(2 * pi() * v);
END;
$$;

CREATE OR REPLACE PROCEDURE faker.choose_value(
    p_locale text, p_seed text, p_position bigint, p_stream text, p_kind text,
    INOUT p_result text DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    u double precision;
BEGIN
    CALL faker.uniform(p_locale, p_seed, p_position, p_stream, u);
    SELECT entries[1 + floor(u * cardinality(entries))::integer] INTO p_result
    FROM faker.lookup_sets WHERE locale = p_locale AND kind = p_kind;
    IF p_result IS NULL THEN
        RAISE EXCEPTION 'Missing lookup kind % for %', p_kind, p_locale USING ERRCODE = '22023';
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_globe(
    p_locale text, p_seed text, p_position bigint,
    INOUT p_result jsonb DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    u double precision;
    v double precision;
BEGIN
    CALL faker.uniform(p_locale, p_seed, p_position, 'globe.latitude', u);
    CALL faker.uniform(p_locale, p_seed, p_position, 'globe.longitude', v);
    p_result := jsonb_build_object(
        'latitude', round(degrees(asin(2*u - 1))::numeric, 6),
        'longitude', round((360*v - 180)::numeric, 6)
    );
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_name(
    p_locale text, p_seed text, p_position bigint,
    INOUT p_result jsonb DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    first_name text;
    middle_name text := '';
    last_name text;
    other_last text;
    title text := '';
    u double precision;
BEGIN
    CALL faker.choose_value(p_locale, p_seed, p_position, 'name.first', 'first_name', first_name);
    CALL faker.choose_value(p_locale, p_seed, p_position, 'name.last', 'last_name', last_name);
    CALL faker.uniform(p_locale, p_seed, p_position, 'name.middle.present', u);
    IF u < 0.35 THEN
        CALL faker.choose_value(p_locale, p_seed, p_position, 'name.middle', 'first_name', middle_name);
    END IF;
    CALL faker.uniform(p_locale, p_seed, p_position, 'name.double_surname.present', u);
    IF u < 0.08 THEN
        CALL faker.choose_value(p_locale, p_seed, p_position, 'name.last.second', 'last_name', other_last);
        IF other_last <> last_name THEN last_name := last_name || '-' || other_last; END IF;
    END IF;
    CALL faker.uniform(p_locale, p_seed, p_position, 'name.title.present', u);
    IF u < 0.10 THEN
        CALL faker.choose_value(p_locale, p_seed, p_position, 'name.title', 'title', title);
    END IF;
    p_result := jsonb_build_object(
        'first_name', first_name, 'middle_name', middle_name, 'last_name', last_name, 'title', title,
        'full_name', concat_ws(' ', nullif(title,''), first_name, nullif(middle_name,''), last_name)
    );
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_address(
    p_locale text, p_seed text, p_position bigint,
    INOUT p_result jsonb DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    config faker.locales%ROWTYPE;
    city faker.cities%ROWTYPE;
    city_index integer;
    city_count integer;
    stem text;
    suffix text;
    street text;
    house integer;
    unit_number integer;
    template text;
    address text;
BEGIN
    SELECT * INTO config FROM faker.locales WHERE code = p_locale;
    IF NOT FOUND THEN RAISE EXCEPTION 'Unsupported locale' USING ERRCODE = '22023'; END IF;
    SELECT count(*) INTO city_count FROM faker.cities WHERE locale = p_locale;
    IF city_count = 0 THEN RAISE EXCEPTION 'Missing cities for locale' USING ERRCODE = '22023'; END IF;
    CALL faker.uniform_integer(p_locale, p_seed, p_position, 'address.city', 1, city_count, city_index);
    -- OFFSET permits user-added ordinal values with gaps while preserving stable order.
    SELECT * INTO city FROM faker.cities WHERE locale = p_locale ORDER BY ordinal OFFSET city_index-1 LIMIT 1;
    CALL faker.choose_value(p_locale, p_seed, p_position, 'address.street.stem', 'street_stem', stem);
    CALL faker.choose_value(p_locale, p_seed, p_position, 'address.street.suffix', 'street_suffix', suffix);
    CALL faker.uniform_integer(p_locale, p_seed, p_position, 'address.house', 1, config.house_number_max, house);
    CALL faker.uniform_integer(p_locale, p_seed, p_position, 'address.unit', 1, 60, unit_number);
    CALL faker.choose_value(p_locale, p_seed, p_position, 'address.format', 'address_format', template);
    street := replace(replace(config.street_template, '{stem}', stem), '{suffix}', suffix);
    address := replace(replace(replace(replace(replace(replace(template,
        '{number}', house::text), '{street}', street), '{city}', city.name), '{region}', city.region), '{postal}', city.postal_code), '{unit}', unit_number::text);
    p_result := jsonb_build_object(
        'address', address, 'city', city.name, 'region', city.region, 'postal_code', city.postal_code,
        'calling_code', city.calling_code, 'street', street, 'house_number', house
    );
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_phone(
    p_locale text, p_seed text, p_position bigint, p_calling_code text,
    INOUT p_result text DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    template text;
    subscriber integer;
BEGIN
    CALL faker.choose_value(p_locale, p_seed, p_position, 'phone.format', 'phone_format', template);
    CALL faker.uniform_integer(p_locale, p_seed, p_position, 'phone.subscriber', 1000000, 9999999, subscriber);
    IF p_calling_code IS NULL OR p_calling_code !~ '^[0-9]+$' THEN
        RAISE EXCEPTION 'Invalid city calling code' USING ERRCODE = '22023';
    END IF;
    p_result := replace(replace(replace(template, '{area}', p_calling_code),
        '{subscriber7}', subscriber::text), '{subscriber4}', right(subscriber::text,4));
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_email(
    p_locale text, p_seed text, p_position bigint, p_first_name text, p_last_name text,
    INOUT p_result text DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    first_ascii text;
    last_ascii text;
    domain_index integer;
    domains text[] := ARRAY['example.com', 'example.org', 'example.net'];
BEGIN
    -- Explicit, versioned transliteration: no OS locale or optional extension.
    first_ascii := lower(p_first_name COLLATE "C");
    last_ascii := lower(p_last_name COLLATE "C");
    first_ascii := replace(replace(replace(replace(replace(replace(replace(first_ascii,
        'Ä','Ae'),'Ö','Oe'),'Ü','Ue'),'ä','ae'),'ö','oe'),'ü','ue'),'ß','ss');
    last_ascii := replace(replace(replace(replace(replace(replace(replace(last_ascii,
        'Ä','Ae'),'Ö','Oe'),'Ü','Ue'),'ä','ae'),'ö','oe'),'ü','ue'),'ß','ss');
    first_ascii := translate(first_ascii,
        'ÀÁÂÃÅàáâãåÈÉÊËèéêëÌÍÎÏìíîïÒÓÔÕØòóôõøÙÚÛùúûÇçÑñÝýÿŠšŽžŁł',
        'AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUuuuCcNnYyySsZzLl');
    last_ascii := translate(last_ascii,
        'ÀÁÂÃÅàáâãåÈÉÊËèéêëÌÍÎÏìíîïÒÓÔÕØòóôõøÙÚÛùúûÇçÑñÝýÿŠšŽžŁł',
        'AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUuuuCcNnYyySsZzLl');
    first_ascii := regexp_replace(lower(first_ascii COLLATE "C"), '[^a-z0-9]', '', 'g');
    last_ascii := regexp_replace(lower(last_ascii COLLATE "C"), '[^a-z0-9]', '', 'g');
    CALL faker.uniform_integer(p_locale, p_seed, p_position, 'email.domain', 1, 3, domain_index);
    -- Position makes addresses unique within a locale+seed dataset. Bound local part to 64.
    p_result := left(coalesce(nullif(first_ascii,''),'user'),22) || '.' ||
        left(coalesce(nullif(last_ascii,''),'person'),28) || '.' || p_position::text || '@' || domains[domain_index];
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_person(
    p_locale text, p_seed text, p_position bigint,
    INOUT p_result jsonb DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    config faker.locales%ROWTYPE;
    person_name jsonb;
    address jsonb;
    globe jsonb;
    phone text;
    email text;
    eye text;
    height double precision;
    weight double precision;
BEGIN
    SELECT * INTO config FROM faker.locales WHERE code = p_locale;
    IF NOT FOUND OR p_position IS NULL OR p_position NOT BETWEEN 1 AND 1000000 THEN
        RAISE EXCEPTION 'Unsupported locale or person position' USING ERRCODE = '22023';
    END IF;
    CALL faker.generate_name(p_locale, p_seed, p_position, person_name);
    CALL faker.generate_address(p_locale, p_seed, p_position, address);
    CALL faker.generate_globe(p_locale, p_seed, p_position, globe);
    CALL faker.normal(p_locale, p_seed, p_position, 'body.height', config.height_mean, config.height_stddev, height);
    CALL faker.normal(p_locale, p_seed, p_position, 'body.weight', config.weight_mean, config.weight_stddev, weight);
    CALL faker.choose_value(p_locale, p_seed, p_position, 'body.eye_color', 'eye_color', eye);
    CALL faker.generate_phone(p_locale, p_seed, p_position, address->>'calling_code', phone);
    CALL faker.generate_email(p_locale, p_seed, p_position, person_name->>'first_name', person_name->>'last_name', email);
    p_result := jsonb_build_object(
        'position', p_position, 'full_name', person_name->>'full_name', 'address', address->>'address',
        'latitude', globe->'latitude', 'longitude', globe->'longitude',
        'height_cm', round(height::numeric,2), 'weight_kg', round(weight::numeric,2),
        'eye_color', eye, 'phone', phone, 'email', email
    );
END;
$$;

CREATE OR REPLACE PROCEDURE faker.list_locales(INOUT p_result jsonb DEFAULT NULL)
LANGUAGE plpgsql AS $$
BEGIN
    SELECT jsonb_build_object('locales', coalesce(jsonb_agg(jsonb_build_object(
        'code', code, 'label', label, 'country', country
    ) ORDER BY code DESC), '[]'::jsonb)) INTO p_result FROM faker.locales;
END;
$$;

CREATE OR REPLACE PROCEDURE faker.generate_batch(
    p_locale text, p_seed text, p_batch integer, p_batch_size integer,
    INOUT p_result jsonb DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    start_position bigint;
    last_position bigint;
    person jsonb;
    people jsonb := '[]'::jsonb;
BEGIN
    IF p_batch IS NULL OR p_batch < 0 OR p_batch_size IS NULL OR p_batch_size NOT BETWEEN 1 AND 100
       OR p_seed IS NULL OR length(p_seed) NOT BETWEEN 1 AND 64 OR p_seed ~ '^[[:space:]]*$'
       OR NOT EXISTS(SELECT 1 FROM faker.locales WHERE code = p_locale) THEN
        RAISE EXCEPTION 'Invalid locale, seed, batch, or batch size' USING ERRCODE = '22023';
    END IF;
    start_position := p_batch::bigint * p_batch_size + 1;
    IF start_position > 1000000 THEN
        RAISE EXCEPTION 'Batch starts beyond the million-person dataset' USING ERRCODE = '22023';
    END IF;
    last_position := least(start_position + p_batch_size - 1, 1000000);
    FOR position IN start_position..last_position LOOP
        CALL faker.generate_person(p_locale, p_seed, position, person);
        people := people || jsonb_build_array(person);
    END LOOP;
    p_result := jsonb_build_object(
        'locale', p_locale, 'seed', p_seed, 'batch', p_batch, 'batch_size', p_batch_size,
        'total', 1000000, 'has_next', last_position < 1000000, 'users', people
    );
END;
$$;
