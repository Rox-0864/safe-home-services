FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir \
        "google-adk>=2.0.0a0" \
        "python-dotenv>=1.0.0" \
        "pydantic>=2.0.0" \
        "sqlmodel>=0.0.22" \
        "streamlit>=1.40.0"

FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY hogar_confianza/ hogar_confianza/
COPY app.py run.py healthcheck.py .env.example ./

EXPOSE 8080

ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python healthcheck.py

CMD ["streamlit", "run", "app.py"]
