from __future__ import annotations

import os
import re
import uuid
from contextlib import contextmanager
from typing import Iterable, Iterator, Sequence

import pandas as pd


def _resolve_dsn(connection_string: str | None = None) -> str | None:
    """Resolve a PostgreSQL DSN from direct string or ${ENV_NAME} placeholder."""
    if connection_string:
        dsn = str(connection_string).strip()
        m = re.fullmatch(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', dsn)
        if m:
            return os.environ.get(m.group(1))
        return os.path.expandvars(dsn)
    return os.environ.get('BITCOIN_DB_URL')


def connect_db(connection_string: str | None = None):
    dsn = _resolve_dsn(connection_string)
    if not dsn or dsn == '${BITCOIN_DB_URL}':
        raise ValueError('Database connection string missing. Set BITCOIN_DB_URL in .env or pass data.raw_db.')
    try:
        import psycopg2
        return psycopg2.connect(dsn)
    except Exception as exc:  # pragma: no cover - requires local DB
        raise ConnectionError(f'Cannot connect to PostgreSQL: {exc}') from exc


def sql_identifier(table_name: str):
    from psycopg2 import sql
    parts = str(table_name).split('.', 1)
    if len(parts) == 2:
        return sql.Identifier(parts[0], parts[1])
    return sql.Identifier(parts[0])


@contextmanager
def named_cursor(conn, prefix: str = 'btcaml_cursor'):
    name = f'{prefix}_{uuid.uuid4().hex[:8]}'
    cur = conn.cursor(name=name)
    try:
        yield cur
    finally:
        cur.close()


def fetch_dataframe(conn, query, params: Sequence | None = None, statement_timeout_ms: int | None = None) -> pd.DataFrame:
    cur = conn.cursor()
    try:
        if statement_timeout_ms and statement_timeout_ms > 0:
            cur.execute('SET statement_timeout = %s', (int(statement_timeout_ms),))
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    finally:
        if statement_timeout_ms and statement_timeout_ms > 0:
            try:
                cur.execute('RESET statement_timeout')
            except Exception:
                conn.rollback()
        cur.close()
    return pd.DataFrame(rows, columns=cols)


def stream_dataframe(conn, query, params: Sequence | None = None, chunk_size: int = 100000) -> Iterator[pd.DataFrame]:
    with named_cursor(conn) as cur:
        cur.itersize = chunk_size
        cur.execute(query, params or ())
        cols = [d[0] for d in cur.description]
        while True:
            rows = cur.fetchmany(chunk_size)
            if not rows:
                break
            yield pd.DataFrame(rows, columns=cols)


def stream_dataframe_regular(
    conn,
    query,
    params: Sequence | None = None,
    chunk_size: int = 100000,
    statement_timeout_ms: int | None = None,
) -> Iterator[pd.DataFrame]:
    """Stream query results with a regular cursor.

    This is used for temp-table joins. It keeps the query in the same session and lets
    PostgreSQL use the indexes on transaction_edges(a) / transaction_edges(b) when present.
    """
    cur = conn.cursor()
    try:
        if statement_timeout_ms and statement_timeout_ms > 0:
            cur.execute('SET statement_timeout = %s', (int(statement_timeout_ms),))
        cur.execute(query, params or ())
        cols = [d[0] for d in cur.description]
        while True:
            rows = cur.fetchmany(chunk_size)
            if not rows:
                break
            yield pd.DataFrame(rows, columns=cols)
    finally:
        if statement_timeout_ms and statement_timeout_ms > 0:
            try:
                cur.execute('RESET statement_timeout')
            except Exception:
                conn.rollback()
        cur.close()


def create_temp_alias_table(conn, aliases: Iterable[int | str], temp_name: str = 'tmp_selected_aliases', batch_size: int = 10000) -> None:
    from psycopg2 import sql
    from psycopg2.extras import execute_values
    cur = conn.cursor()
    try:
        cur.execute(sql.SQL('DROP TABLE IF EXISTS {}').format(sql.Identifier(temp_name)))
        cur.execute(sql.SQL('CREATE TEMP TABLE {} (alias BIGINT PRIMARY KEY) ON COMMIT DROP').format(sql.Identifier(temp_name)))
        insert_sql = sql.SQL('INSERT INTO {} (alias) VALUES %s ON CONFLICT DO NOTHING').format(sql.Identifier(temp_name)).as_string(conn)
        batch = []
        for a in aliases:
            if a is None:
                continue
            batch.append((int(a),))
            if len(batch) >= batch_size:
                execute_values(cur, insert_sql, batch, page_size=batch_size)
                batch.clear()
        if batch:
            execute_values(cur, insert_sql, batch, page_size=batch_size)
        cur.execute(sql.SQL('ANALYZE {}').format(sql.Identifier(temp_name)))
    finally:
        cur.close()
