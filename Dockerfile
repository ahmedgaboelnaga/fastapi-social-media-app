FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory in the container
WORKDIR /code

COPY ./pyproject.toml ./uv.lock ./

RUN uv sync --frozen --no-cache --no-dev

# Copy the current directory contents into the container at /code
COPY . .

# Expose the app port
EXPOSE 80

CMD ["/code/.venv/bin/gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
