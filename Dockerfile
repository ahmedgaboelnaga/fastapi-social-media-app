FROM python:3.11-slim

# Install system dependencies for psycopg and building packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

COPY ./pyproject.toml ./uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

COPY . .

COPY entrypoint.sh /
RUN sed -i 's/\r$//g' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
