import base64
import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from hogar_confianza.agent import root_agent
from hogar_confianza.database.engine import get_engine, init_db, set_db_engine
from hogar_confianza.database.seed import seed_providers

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = get_engine()
init_db(engine)
seed_providers(engine)
set_db_engine(engine)

app = FastAPI(title="HogarConfianza API", version="1.0.0")

session_service = InMemorySessionService()

runner = Runner(
    app_name="hogar-confianza",
    agent=root_agent,
    session_service=session_service,
)


@app.get("/health")
async def health():
    return {"status": "ok", "app": "hogar-confianza"}


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_id = body.get("user_id", "anonymous")
    session_id = body.get("session_id", "default")
    message = body.get("message", "")

    try:
        await session_service.create_session(
            app_name="hogar-confianza",
            user_id=user_id,
            session_id=session_id,
        )
    except Exception:
        pass

    user_msg = Content(parts=[Part(text=message)], role="user")

    responses = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_msg,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    responses.append(part.text)

    return {"response": " ".join(responses)}


@app.post("/trigger/pubsub")
async def trigger_pubsub(request: Request):
    body = await request.json()
    subscription = body.get("subscription", "unknown")

    sub_name = subscription.split("/")[-1] if "/" in subscription else subscription

    message_data = body.get("message", {}).get("data", "")
    try:
        decoded = base64.b64decode(message_data).decode("utf-8")
        payload = json.loads(decoded)
    except Exception:
        payload = {"raw": message_data}

    session_id = f"pubsub-{sub_name}-{hash(str(payload)) % 10000}"

    try:
        await session_service.create_session(
            app_name="hogar-confianza",
            user_id=sub_name,
            session_id=session_id,
        )
    except Exception:
        pass

    user_msg = Content(parts=[Part(text=json.dumps(payload, ensure_ascii=False))], role="user")

    responses = []
    async for event in runner.run_async(
        user_id=sub_name,
        session_id=session_id,
        new_message=user_msg,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    responses.append(part.text)

    return {"session_id": session_id, "response": " ".join(responses)}
