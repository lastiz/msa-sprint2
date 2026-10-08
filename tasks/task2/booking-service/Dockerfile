FROM ghcr.io/astral-sh/uv:0.11.28 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY booking ./booking
USER 10001:10001
EXPOSE 9090
CMD ["/app/.venv/bin/python", "-m", "booking"]
