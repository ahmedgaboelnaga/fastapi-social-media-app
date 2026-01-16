#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

# Wait for PostgreSQL
/code/.venv/bin/python << 'END'
import os
import sys
import time
import psycopg

def wait_for_postgres(timeout: int = 30, retry_interval: int = 5):
    start_time = time.time()
    
    host = os.getenv("DATABASE_HOSTNAME")
    port = int(os.getenv("DATABASE_PORT", 5432))
    user = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    dbname = os.getenv("DATABASE_NAME")
    
    while True:
        try:
            conn = psycopg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=dbname,
            )
            conn.close()
            return
        except psycopg.OperationalError as error:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                sys.stderr.write(f"Timed out waiting for PostgreSQL after {elapsed:.1f} seconds: {error}\n")
                sys.exit(1)
            sys.stderr.write(f"Waiting for PostgreSQL ({elapsed:.1f}s elapsed)...\n")
            time.sleep(retry_interval)

wait_for_postgres(timeout=30, retry_interval=5)
END

>&2 echo 'PostgreSQL is ready to accept connections'

# Run migrations
/code/.venv/bin/alembic upgrade head

# Execute the command passed to the container
exec "$@"
