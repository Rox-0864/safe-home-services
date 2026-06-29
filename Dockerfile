FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY hogar_confianza/ hogar_confianza/
RUN pip install --no-cache-dir setuptools wheel && \
    pip install --no-cache-dir .

FROM python:3.12-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local /usr/local

COPY app.py run.py healthcheck.py ./

EXPOSE 8080

ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python healthcheck.py

CMD ["streamlit", "run", "app.py"]
