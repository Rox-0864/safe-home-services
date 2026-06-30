"""Generate evaluation traces by running scenarios through the agent."""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from google.adk import Runner

from hogar_confianza.agent import root_agent

DATASET_PATH = os.path.join(os.path.dirname(__file__), "datasets", "basic-dataset.json")
TRACES_PATH = os.path.join(os.path.dirname(__file__), "../../artifacts/traces/generated_traces.json")


async def generate_traces():
    with open(DATASET_PATH, "r") as f:
        scenarios = json.load(f)

    runner = Runner(
        app_name="hogar-confianza-eval",
        agent=root_agent,
    )

    traces = []
    for scenario in scenarios:
        print(f"Running: {scenario['name']}...")
        trace = {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "input": scenario["input"],
            "expected_behavior": scenario["expected_behavior"],
            "events": [],
            "response": "",
        }

        try:
            async for event in runner.run_async(
                user_id="eval-user",
                session_id=f"eval-{scenario['id']}",
                new_message=scenario["input"],
            ):
                event_data = {
                    "id": event.id,
                    "content": str(event.content) if event.content else None,
                    "actions": [str(a) for a in (event.actions or [])],
                }
                trace["events"].append(event_data)

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            trace["response"] += part.text

            trace["status"] = "completed"
        except Exception as e:
            trace["status"] = "error"
            trace["error"] = str(e)

        traces.append(trace)

    os.makedirs(os.path.dirname(TRACES_PATH), exist_ok=True)
    with open(TRACES_PATH, "w") as f:
        json.dump(traces, f, indent=2, ensure_ascii=False)

    print(f"\nGenerated {len(traces)} traces → {TRACES_PATH}")
    return traces


if __name__ == "__main__":
    asyncio.run(generate_traces())
