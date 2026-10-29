"""Database transport and input types shared by the API and Python HTML pages."""

import logging
import os
from typing import Annotated

import psycopg
from fastapi import HTTPException, Query


logger = logging.getLogger(__name__)
Seed = Annotated[str, Query(min_length=1, max_length=64)]
Locale = Annotated[str, Query(min_length=1, max_length=16)]
Batch = Annotated[int, Query(ge=0, le=999999)]
BatchSize = Annotated[int, Query(ge=1, le=100)]
TextPosition = Annotated[int, Query(ge=1, le=1_000_000)]
WordCount = Annotated[int, Query(ge=10, le=500)]


def database_query(query: str, parameters: tuple = ()):
    """A short transaction with bound arguments, safe for transaction poolers."""
    try:
        with psycopg.connect(
            os.getenv("DATABASE_URL", "postgresql://faker:faker@localhost:5432/faker"),
            connect_timeout=3, autocommit=False,
        ) as connection:
            # PgBouncer rejects statement_timeout in connection startup options.
            # SET LOCAL pins these settings to this transaction without leaking
            # them to the next request that reuses the pooled server connection.
            connection.execute("SET LOCAL statement_timeout = '15s'")
            connection.execute("SET LOCAL TIME ZONE 'UTC'")
            return connection.execute(query, parameters).fetchone()[0]
    except psycopg.errors.InvalidParameterValue as error:
        raise HTTPException(422, "Invalid locale, seed, or generation parameters.") from error
    except psycopg.Error as error:
        logger.warning("Database operation failed (%s)", type(error).__name__)
        raise HTTPException(503, "Database is temporarily unavailable.") from error


def locales():
    return database_query("CALL faker.list_locales(NULL)")


def users(locale="en_US", seed="42", batch=0, batch_size=10):
    if not seed.strip() or batch * batch_size >= 1_000_000:
        raise HTTPException(422, "Seed must be nonempty and the batch must start before position 1,000,001.")
    return database_query("CALL faker.generate_batch(%s,%s,%s,%s,NULL)", (locale, seed, batch, batch_size))


def generate_text(locale="en_US", seed="42", position=1, word_count=80):
    if not seed.strip():
        raise HTTPException(422, "Seed must contain a non-whitespace character.")
    return database_query("CALL faker.generate_text(%s,%s,%s,%s,NULL)", (locale, seed, position, word_count))
