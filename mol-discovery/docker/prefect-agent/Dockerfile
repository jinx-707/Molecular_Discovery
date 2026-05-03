FROM prefecthq/prefect:2-python3.11

WORKDIR /app

# Copy code
COPY backend /app/backend
COPY pyproject.toml poetry.lock /app/

# Install deps
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Agent config
COPY docker/prefect-agent/prefect-agent.toml /root/.prefect/prefect-agent.toml

CMD ["prefect", "agent", "local"]

