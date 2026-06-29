.PHONY: install run web streamlit test clean docker-build docker-push deploy

PROJECT_ID = hogar-confianza
REGION = us-central1
REPO = hogar-confianza
IMAGE = $(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(REPO)/hogar-confianza
TAG = latest
SERVICE_NAME = hogar-confianza

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
	docker build -t $(IMAGE):$(TAG) .

docker-push:
	docker push $(IMAGE):$(TAG)

deploy:
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE):$(TAG) \
		--region $(REGION) \
		--port 8080 \
		--allow-unauthenticated

deploy-with-env:
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE):$(TAG) \
		--region $(REGION) \
		--port 8080 \
		--allow-unauthenticated \
		--set-env-vars "GOOGLE_API_KEY=$$(cat .env.api-key)"

test:
	pytest tests/ -v

clean:
	rm -rf __pycache__ .venv artifacts/ *.egg-info
