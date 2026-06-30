import asyncio
import json

import streamlit as st
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from sqlmodel import Session, select

from hogar_confianza.agent import root_agent
from hogar_confianza.database.engine import get_db_engine, get_engine, init_db, set_db_engine
from hogar_confianza.database.models import BookingDB
from hogar_confianza.database.seed import seed_providers
from hogar_confianza.i18n import get_language, get_ui, set_language
from hogar_confianza.tools.safety_tools import check_in_provider, check_out_provider, trigger_panic_button

st.set_page_config(page_title=get_ui("page_title"), page_icon="🏠", layout="wide")

USER_ID = "web-user-001"
SESSION_ID = "web-session-001"


@st.cache_resource
def init_app():
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
    return runner, session_service


def run_agent(message: str, runner, session_service) -> str:
    async def _run():
        try:
            await session_service.create_session(
                app_name="hogar-confianza",
                user_id=USER_ID,
                session_id=SESSION_ID,
            )
        except Exception:
            pass
        user_msg = Content(parts=[Part(text=message)], role="user")
        responses = []
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=user_msg,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        responses.append(part.text)
        return " ".join(responses)

    return asyncio.run(_run())


def render_provider_cards(text: str):
    try:
        providers = json.loads(text)
        if not isinstance(providers, list) or not providers:
            return False
        if not isinstance(providers[0], dict) or "id" not in providers[0]:
            return False
        cols = st.columns(min(3, len(providers)))
        for i, p in enumerate(providers):
            with cols[i % 3]:
                verified = get_ui("verified")
                not_verified = get_ui("not_verified")
                badge = f"✅ {verified}" if p.get("verified") else f"⚠️ {not_verified}"
                has_ins = get_ui("with_insurance")
                no_ins = get_ui("without_insurance")
                insurance = f"🛡️ {has_ins}" if p.get("has_insurance") else f"❌ {no_ins}"
                st.markdown(f"**{p['name']}**")
                st.markdown(f"⭐ {p.get('rating', 'N/A')} | Trust: {p.get('trust_score', 'N/A')}")
                yrs = get_ui("years")
                jbs = get_ui("jobs")
                st.markdown(f"📅 {p.get('years_experience', 0)} {yrs} | {p.get('completed_jobs', 0)} {jbs}")
                st.markdown(f"{badge} | {insurance}")
                if st.button(f"{get_ui('select')} {p['name']}", key=f"sel_{p['id']}"):
                    st.session_state.selected_provider = p
                    st.rerun()
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def render_booking_info(text: str):
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            return False
        if "booking_id" in data:
            st.success(f"📋 {get_ui('bookings_title')} {data['booking_id']}")
            st.markdown(f"**{get_ui('status')}**: {data.get('status', 'N/A')}")
            if "amount_held" in data:
                st.markdown(f"**{get_ui('amount')}**: ${data['amount_held']:,.2f} MXN")
            if "message" in data:
                st.info(data["message"])
            return True
    except (json.JSONDecodeError, TypeError):
        return False


def parse_and_render(text: str):
    if render_provider_cards(text):
        return
    if render_booking_info(text):
        return
    st.markdown(text)


def get_user_bookings() -> list:
    engine = get_db_engine()
    with Session(engine) as session:
        stmt = select(BookingDB)
        bookings = session.exec(stmt).all()
        return bookings


def sidebar_ui():
    with st.sidebar:
        st.title("🏠 HogarConfianza")

        lang = get_language()
        cols = st.columns([1, 1])
        with cols[0]:
            if st.button("🇪🇸 ES", type="primary" if lang == "es" else "secondary", use_container_width=True):
                set_language("es")
                st.session_state.language = "es"
                st.rerun()
        with cols[1]:
            if st.button("🇬🇧 EN", type="primary" if lang == "en" else "secondary", use_container_width=True):
                set_language("en")
                st.session_state.language = "en"
                st.rerun()

        st.divider()

        if "user_name" not in st.session_state:
            st.subheader(get_ui("register_title"))
            name = st.text_input(get_ui("name_label"), key="reg_name")
            phone = st.text_input(get_ui("phone_label"), key="reg_phone")
            if st.button(get_ui("register_button")) and name and phone:
                st.session_state.user_name = name
                st.session_state.user_phone = phone
                st.rerun()
        else:
            st.success(f"👤 {st.session_state.user_name}")
            st.caption(f"📱 {st.session_state.user_phone}")

        st.divider()
        st.subheader(f"📋 {get_ui('bookings_title')}")

        bookings = get_user_bookings()
        if not bookings:
            st.caption(get_ui("no_bookings"))
        else:
            for b in bookings:
                status_icon = {
                    get_ui("booking_status_pending"): "⏳",
                    get_ui("booking_status_confirmed"): "✅",
                    get_ui("booking_status_completed"): "✔️",
                    get_ui("booking_status_rejected"): "❌",
                    get_ui("booking_status_held"): "🔄",
                }.get(b.status, "❓")
                with st.expander(f"{status_icon} {b.service} - {b.id}"):
                    st.markdown(f"**{get_ui('status')}**: {b.status}")
                    st.markdown(f"**{get_ui('provider')}**: {b.provider_id}")
                    st.markdown(f"**{get_ui('date')}**: {b.scheduled_date} {b.scheduled_time}")
                    st.markdown(f"**{get_ui('amount')}**: ${b.amount:,.2f} MXN")
                    if b.status == get_ui("booking_status_confirmed"):
                        if st.button(f"🔐 {get_ui('check_in')}", key=f"ci_{b.id}"):
                            result = json.loads(check_in_provider(b.id, b.provider_id, "Domicilio"))
                            st.success(result.get("message", "Check-in realizado"))
                        if st.button(f"🔓 {get_ui('check_out')}", key=f"co_{b.id}"):
                            result = json.loads(check_out_provider(b.id, b.provider_id, 2.0))
                            st.success(result.get("message", "Check-out realizado"))

        st.divider()
        if bookings:
            if st.button(f"🚨 {get_ui('panic_button')}", type="primary", use_container_width=True):
                for b in bookings:
                    if b.status == get_ui("booking_status_confirmed"):
                        result = json.loads(trigger_panic_button(b.id, "Domicilio"))
                        st.error(result.get("message", "🚨 ALERTA DE EMERGENCIA"))
                        break


def main():
    lang = st.query_params.get("lang", st.session_state.get("language", "es"))
    st.session_state.language = lang
    set_language(lang)

    runner, session_service = init_app()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    sidebar_ui()

    chat_col, _ = st.columns([3, 1])

    with chat_col:
        st.title(f"💬 {get_ui('app_title')}")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    parse_and_render(msg["content"])
                else:
                    st.markdown(msg["content"])

        if prompt := st.chat_input(get_ui("chat_input")):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner(get_ui("spinner")):
                    response = run_agent(prompt, runner, session_service)
                parse_and_render(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()


if __name__ == "__main__":
    main()
