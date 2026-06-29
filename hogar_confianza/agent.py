from dotenv import load_dotenv
from google.adk import Agent

from hogar_confianza._model import resolve_model_with_fallback
from hogar_confianza.agents.booking import booking_agent
from hogar_confianza.agents.matching import matching_agent
from hogar_confianza.agents.safety import safety_agent
from hogar_confianza.agents.triage import triage_agent
from hogar_confianza.i18n import get_prompt, get_ui
from hogar_confianza.security.pii_redactor import SecurityScreen

load_dotenv()

SECURITY_SCREEN = SecurityScreen()


def before_model_callback(*, callback_context, llm_request):
    user_inputs = []
    for msg in llm_request.contents or []:
        role = getattr(msg, 'role', None)
        if role == 'user' and msg.parts:
            for part in msg.parts:
                text = getattr(part, 'text', None)
                if text:
                    user_inputs.append(text)

    for text in user_inputs:
        result = SECURITY_SCREEN.process(text)
        if result["injection_detected"]:
            from google.adk.models.llm_response import LlmResponse
            from google.genai.types import Content, Part
            warning = f"🚨 **{get_ui('security_alert_title')}**: {get_ui('security_alert_msg')}"
            return LlmResponse(
                content=Content(parts=[Part(text=warning)])
            )

    return None


root_agent = Agent(
    name="root_agent",
    model=resolve_model_with_fallback(),
    instruction=lambda _ctx: get_prompt("root"),
    sub_agents=[triage_agent, matching_agent, safety_agent, booking_agent],
    before_model_callback=before_model_callback,
)
