-- Benchmark the real contact procedure inside PostgreSQL, excluding network/UI.
CREATE OR REPLACE PROCEDURE faker.benchmark_users(
    p_locale text, p_seed text, p_users integer DEFAULT 10000,
    p_batch_size integer DEFAULT 100, p_repetitions integer DEFAULT 3,
    p_warmup_batches integer DEFAULT 5, INOUT p_result jsonb DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    payload jsonb;
    runs jsonb := '[]'::jsonb;
    started timestamptz;
    elapsed double precision;
    total_seconds double precision := 0;
    generated integer;
    batches integer;
    rates double precision[] := ARRAY[]::double precision[];
    median_rate double precision;
    generator text;
BEGIN
    IF p_users IS NULL OR p_users NOT BETWEEN 100 AND 1000000
       OR p_batch_size IS NULL OR p_batch_size NOT BETWEEN 1 AND 100
       OR p_repetitions IS NULL OR p_repetitions NOT BETWEEN 1 AND 10
       OR p_warmup_batches IS NULL OR p_warmup_batches NOT BETWEEN 0 AND 100 THEN
        RAISE EXCEPTION 'Invalid benchmark size, batch size, repetitions, or warmup' USING ERRCODE = '22023';
    END IF;
    IF p_users % p_batch_size <> 0 THEN
        RAISE EXCEPTION 'Benchmark users must be a multiple of batch size' USING ERRCODE = '22023';
    END IF;
    -- Validate locale/seed even when warmup is disabled; exclude this call.
    CALL faker.generate_batch(p_locale, p_seed, 0, p_batch_size, payload);
    SELECT generator_version INTO generator FROM faker.locales WHERE code = p_locale;
    IF p_warmup_batches > 0 THEN
        FOR batch IN 0..p_warmup_batches - 1 LOOP
            CALL faker.generate_batch(p_locale, p_seed, batch, p_batch_size, payload);
        END LOOP;
    END IF;
    batches := p_users / p_batch_size;
    FOR repetition IN 1..p_repetitions LOOP
        generated := 0;
        started := clock_timestamp();
        FOR batch IN 0..batches - 1 LOOP
            CALL faker.generate_batch(p_locale, p_seed, batch, p_batch_size, payload);
            generated := generated + jsonb_array_length(payload->'users');
        END LOOP;
        elapsed := extract(epoch FROM clock_timestamp() - started)::double precision;
        IF generated <> p_users OR elapsed <= 0 THEN
            RAISE EXCEPTION 'Benchmark could not measure the requested complete workload';
        END IF;
        rates := array_append(rates, generated / elapsed);
        total_seconds := total_seconds + elapsed;
        runs := runs || jsonb_build_array(jsonb_build_object(
            'run', repetition, 'users', generated, 'seconds', elapsed,
            'users_per_second', generated / elapsed
        ));
    END LOOP;
    SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY rate)
      INTO median_rate FROM unnest(rates) AS samples(rate);
    p_result := jsonb_build_object(
        'locale', p_locale, 'seed', p_seed, 'generator_version', generator,
        'users_per_run', p_users, 'batch_size', p_batch_size,
        'warmup_batches', p_warmup_batches, 'validation_batches', 1,
        'runs', runs, 'median_users_per_second', median_rate,
        'total_generated', p_users * p_repetitions, 'total_seconds', total_seconds,
        'pooled_users_per_second', (p_users::double precision * p_repetitions) / total_seconds,
        'measurement', 'PostgreSQL clock_timestamp; complete generate_batch calls and JSON assembly'
    );
END;
$$;
