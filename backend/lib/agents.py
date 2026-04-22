from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
import lib.state as state
import lib.prompts as prompts
from lib.state import AgentState
import lib.chatlib as chatlib

# Load environment variables from .env file
load_dotenv()

# Load LLMs
reasoning_llm = chatlib.get_chat_model("BSU_").llm
macro_formatter = chatlib.get_chat_model("API_").llm.with_structured_output(state.MacroCycle)
meso_fortmatter = chatlib.get_chat_model("API_").llm.with_structured_output(state.MesoCycle)
#micro_llm = chatlib.get_chat_model("BSU_").llm.with_structured_output(state.MicroCycle, method="json_mode")

def macro_agent(state: AgentState) -> dict:

    # Grab athlete_profile from state
    profile = state["athlete_profile"]

    # Inject reasoning prompt and profile into the llm prompt
    reasoning_messages = [
        SystemMessage(prompts.MACRO_REASONING_PROMPT),
        HumanMessage(f"""
            Please build a macro training cycle for this athlete:
            Athlete Profile: {profile}
        """
        )
    ]
    # Generate a plaintext macro proposal
    macro_proposal = reasoning_llm.invoke(reasoning_messages)
    structured_messages = [
        SystemMessage(prompts.MACRO_SUMMARIZER_PROMPT),
        HumanMessage(macro_proposal.content)
    ]
    MAX_RETRIES = 3
    last_err = None

    # Try to abide by the Pydantic structure defined in state.py (3 attempts)
    for attempt in range(MAX_RETRIES):
        try:
            # Take the unstructured plan and generate a plan based off of it
            structured_plan = macro_formatter.invoke(structured_messages)
            if structured_plan:
                return {"macro_plan": structured_plan, "error": None}

        # Catch exception and append it to the structured message to give structure llm info on what to fix
        except Exception as e:
            print(f"Exception on attempt {attempt + 1}: {type(e).__name__}: {e}")
            last_err = str(e)
            structured_messages.append(HumanMessage(f"Your response failed validation: {last_err}. Please fix it."))

    print(f"All retries exhausted. Last error: {last_err}")
    return {"macro_plan": None, "error" : f"macro_agent failed after {MAX_RETRIES} attempts: {last_err}"}

def meso_agent(state: AgentState):
    profile = state["athlete_profile"]
    macro_plan = state["macro_plan"]

    meso_plans = []

    for stub in macro_plan.mesocycles:
        reasoning_messages = [
            SystemMessage(),
            HumanMessage(f"""
                Athlete profile: {profile}
                Macro Plan: {macro_plan}

                Please build a detailed mesocycle plan for this phase:
                Phase: {stub.phase}
                Number of weeks: {stub.num_weeks}
                Focus: {stub.focus}
                Start Date: {stub.start_date}
                End Date: {stub.end_date}
                        """)
        ]