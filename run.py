import asyncio
import os
from dotenv import load_dotenv

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from hogar_confianza.agent import root_agent
from hogar_confianza.database.engine import get_engine, init_db, set_db_engine
from hogar_confianza.database.seed import seed_providers


load_dotenv()


async def main():
    engine = get_engine()
    init_db(engine)
    seed_providers(engine)
    set_db_engine(engine)

    session_service = InMemorySessionService()

    runner = Runner(
        app_name="hogar-confianza",
        agent=root_agent,
        session_service=session_service,
    )

    user_id = "test-user-001"
    session_id = "session-001"

    await session_service.create_session(
        app_name="hogar-confianza",
        user_id=user_id,
        session_id=session_id,
    )

    print("🏠 HogarConfianza - Asistente de Servicios del Hogar")
    print("Escribe 'salir' para terminar\n")

    while True:
        user_input = input("👤 Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            break

        user_msg = Content(parts=[Part(text=user_input)], role="user")

        print("\n🤖 HogarConfianza: ", end="", flush=True)
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_msg,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    asyncio.run(main())
