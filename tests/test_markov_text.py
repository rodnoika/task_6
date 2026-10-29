"""Acceptance checks for real, locale-specific SQL Markov text generation."""

from collections import Counter

import pytest


@pytest.mark.live
@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_text_is_localized_reproducible_and_exact_length(api, locale):
    args = dict(locale=locale, seed="Markov Grüße & 42", position=7, word_count=80)
    status, text = api.get("/api/text", **args)
    assert status == 200, text
    assert text["locale"] == locale and text["seed"] == args["seed"]
    assert text["position"] == 7 and text["word_count"] == 80
    assert text["chain_order"] == 2 and text["model_version"] == "sql-markov-v1"
    assert len(text["text"].split()) == 80
    assert text["text"][-1] in ".!?"
    assert "lorem" not in text["text"].lower()
    assert api.get("/api/text", **args)[1] == text
    assert api.get("/api/text", **{**args, "position": 8})[1]["text"] != text["text"]
    assert api.get("/api/text", **{**args, "seed": "another seed"})[1]["text"] != text["text"]


@pytest.mark.live
@pytest.mark.parametrize("arguments", [
    {"locale": "fr_FR"}, {"seed": ""}, {"seed": " \t "},
    {"seed": "x" * 65}, {"position": 0}, {"position": 1_000_001},
    {"word_count": 9}, {"word_count": 501}, {"word_count": "2.5"},
])
def test_invalid_text_requests_are_rejected(api, arguments):
    status, body = api.get("/api/text", **arguments)
    assert status == 422, body


@pytest.mark.database
@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_training_counts_and_generated_transitions_match_the_corpus(db_connect, locale):
    with db_connect() as connection:
        corpus = connection.execute(
            "SELECT corpus FROM faker.text_corpora WHERE locale=%s AND model_version='sql-markov-v1'",
            (locale,),
        ).fetchone()[0]
        actual = {(a, b, token): weight for a, b, token, weight in connection.execute(
            "SELECT previous_first,previous_second,next_token,weight FROM faker.markov_transitions "
            "WHERE locale=%s AND model_version='sql-markov-v1'", (locale,),
        )}
        expected = Counter()
        for sentence in corpus.splitlines():
            words = sentence.split()
            history = ["<s>", "<s>"]
            for word in words:
                expected[(*history, word)] += 1
                history = [history[1], word]
        assert actual == expected
        # Shared contexts must branch: a list of whole predefined sentences is insufficient.
        successors = Counter((a, b) for a, b, _ in actual)
        assert sum(count > 1 for count in successors.values()) >= 15
        payload = connection.execute(
            "CALL faker.generate_text(%s,%s,%s,%s,NULL)", (locale, "walk-check", 11, 500),
        ).fetchone()[0]
        history = ["<s>", "<s>"]
        # The last word may receive a final full stop when the length cuts a sentence.
        for word in payload["text"].split()[:-1]:
            assert (*history, word) in expected
            history = ["<s>", "<s>"] if word.endswith((".", "!", "?")) else [history[1], word]
        repeated = connection.execute(
            "CALL faker.generate_text(%s,%s,%s,%s,NULL)", (locale, "walk-check", 11, 80),
        ).fetchone()[0]
        assert repeated["text"].split()[:-1] == payload["text"].split()[:79]


@pytest.mark.database
@pytest.mark.live
@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_text_api_returns_the_actual_stored_procedure_result(api, db_connect, locale):
    args = dict(locale=locale, seed="direct-text", position=1_000_000, word_count=10)
    with db_connect() as connection:
        sql = connection.execute(
            "CALL faker.generate_text(%s,%s,%s,%s,NULL)", tuple(args.values()),
        ).fetchone()[0]
    assert api.get("/api/text", **args) == (200, sql)


@pytest.mark.database
def test_weighted_sampling_follows_observation_frequency(db_connect):
    with db_connect() as connection:
        try:
            connection.execute("INSERT INTO faker.text_corpora VALUES ('en_US','qa-weighted','A B.','Temporary test corpus')")
            connection.execute(
                "INSERT INTO faker.markov_transitions VALUES "
                "('en_US','qa-weighted','<s>','<s>','Frequent',9),"
                "('en_US','qa-weighted','<s>','<s>','Rare',1)"
            )
            connection.execute("""
                DO $$ DECLARE token text; frequent integer:=0;
                BEGIN
                    FOR i IN 1..1000 LOOP
                        CALL faker.markov_next('en_US','weight-check',i,1,'<s>','<s>','qa-weighted',token);
                        IF token='Frequent' THEN frequent:=frequent+1; END IF;
                    END LOOP;
                    IF frequent NOT BETWEEN 850 AND 950 THEN
                        RAISE EXCEPTION 'Weighted draw frequency is wrong: %',frequent;
                    END IF;
                END $$;
            """)
        finally:
            connection.rollback()


@pytest.mark.live
def test_text_generation_does_not_change_the_contact_sequence(api):
    before = api.users(seed="independent-stream")
    assert api.get("/api/text", locale="de_DE", seed="independent-stream", word_count=500)[0] == 200
    assert api.users(seed="independent-stream") == before
