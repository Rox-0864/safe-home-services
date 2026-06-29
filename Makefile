.PHONY: install run web streamlit test clean docker-build docker-build-cloud

install:
	pip install -e .
	pip install "mcp[cli]" uvicorn

run:
	python run.py

web:
	adk web .

playground:
	uvicorn hogar_confianza.fast_api_app:app --host 0.0.0.0 --port 8080 --reload

mcp-server:
	python -m hogar_confianza.mcp_server.server

streamlit-run:
	streamlit run app.py

docker-build:
	docker build -t hogar-confianza .

docker-run:
	docker run -p 8080:8080 --env-file .env hogar-confianza

docker-build-cloud:
	docker build -t gcr.io/$$(gcloud config get-value project)/hogar-confianza .
	docker push gcr.io/$$(gcloud config get-value project)/hogar-confianza
	gcloud run deploy hogar-confianza \
		--image gcr.io/$$(gcloud config get-value project)/hogar-confianza \
		--port 8080 \
		--set-env-vars "DATABASE_URL=$$(gcloud secrets versions access latest --secret=hogar-confianza-db-url)"

test:
	pytest tests/ -v

clean:
	rm -rf __pycache__ .venv artifacts/ *.egg-info
