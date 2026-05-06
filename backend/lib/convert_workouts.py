from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
import chatlib as chatlib
import json
import os

load_dotenv()

SYSTEM_PROMPT = """
You are a swim workout converter. 
When given a swim workout, you return ONLY valid JSON with no preamble, 
no explanation, and no markdown backticks. Nothing but raw JSON.
"""

llm = chatlib.get_chat_model("BSU_")    # claude 4.6 sonnet

def convert_workout(raw_txt: str) -> dict:
    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(f"""
            Convert this swim workout into structured JSON exactly matching this schema:

            {{
                "phase": "General Preparation|Specific Preparation|Taper|Deload",
                "focus": "Aerobic|Anaerobic|Threshold|Technique|Taper|Power|Recovery",
                "stroke_focus": "Freestyle|Butterfly|Backstroke|Breaststroke|IM",
                "total_yardage": int,
                "sections": [
                    {{
                        "name": "Warm Up|Technique Set|Pre Set|Main Set|Post Set|Cool Down",
                        "items": [
                            {{
                                "reps": int,
                                "sets": int,
                                "distance": int,
                                "interval": "MM:SS or null",
                                "description": "any notes or drill details"
                            }}
                        ]
                    }}
                ]
            }}

            Return ONLY valid JSON, no preamble, no markdown backticks.

            Workout:
            {raw_txt}
            """)
        ]

    res = llm.invoke(messages=messages)
    content = res.content

    if isinstance(content, list):
        content = content[0].get('text', '')

    content = content.strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    print(repr(content[:100]))
    return json.loads(content)


# batch process individual files
input_dir = 'swim_sets/'
output_dir = 'structured/'
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.endswith('.txt'):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename.replace('.txt', '.json'))

        # skip if already converted
        if os.path.exists(output_path):
            print(f"Skipping {filename} - already converted")
            continue

        with open(input_path, 'r') as f:
            raw = f.read()

        try:
            structured = convert_workout(raw)
            with open(output_path, 'w') as f:
                json.dump(structured, f, indent=2)
            print(f"Converted {filename}")
        except Exception as e:
            print(f"Failed {filename}: {e}")