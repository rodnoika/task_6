-- Run after initialization: psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/smoke_checks.sql
DO $$
DECLARE
    a jsonb;
    b jsonb;
    c jsonb;
    u double precision;
    person jsonb;
BEGIN
    CALL faker.generate_batch('en_US', '42', 0, 10, a);
    CALL faker.generate_batch('en_US', '42', 0, 10, b);
    IF a <> b THEN RAISE EXCEPTION 'Identical requests differ'; END IF;
    CALL faker.generate_batch('en_US', '42', 1, 5, c);
    IF (a->'users')->5 <> (c->'users')->0 THEN
        RAISE EXCEPTION 'Changing page size changed absolute person 6';
    END IF;
    IF (a->'users'->0->>'position')::integer <> 1 THEN
        RAISE EXCEPTION 'Positions must be one-based';
    END IF;
    CALL faker.generate_batch('de_DE', '42', 0, 10, c);
    IF a->'users' = c->'users' THEN RAISE EXCEPTION 'Locale has no effect'; END IF;
    FOR i IN 1..100 LOOP
        CALL faker.uniform('en_US', '42', i, 'smoke', u);
        IF u <= 0 OR u >= 1 THEN RAISE EXCEPTION 'Uniform outside open interval'; END IF;
    END LOOP;
    FOREACH person IN ARRAY ARRAY(SELECT jsonb_array_elements(a->'users')) LOOP
        IF (person->>'latitude')::numeric NOT BETWEEN -90 AND 90
           OR (person->>'longitude')::numeric NOT BETWEEN -180 AND 180
           OR person->>'email' !~ '^[a-z0-9.]+@example\.(com|org|net)$' THEN
            RAISE EXCEPTION 'Malformed generated person: %', person;
        END IF;
    END LOOP;
    CALL faker.generate_batch('en_US', '42', 333333, 3, c);
    IF jsonb_array_length(c->'users') <> 1 OR (c->>'has_next')::boolean THEN
        RAISE EXCEPTION 'Final partial batch is incorrect';
    END IF;
END;
$$;
