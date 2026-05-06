from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
import lib.state as state
import lib.prompts as prompts
from lib.state import AgentState
import lib.chatlib as chatlib
from lib.rag import retrieve_workouts

# Load environment variables from .env file
load_dotenv()

# Load LLMs
reasoning_llm = chatlib.get_chat_model("BSU_").llm      # claude
macro_formatter = chatlib.get_chat_model("API_").llm.with_structured_output(state.MacroCycle)       # gemma4
meso_fortmatter = chatlib.get_chat_model("API_").llm.with_structured_output(state.MesoCycle)
micro_llm = chatlib.get_chat_model("API_").llm.with_structured_output(state.WorkoutStub)

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

# plans the microcycle stubs that make up a mesocycle.
def meso_agent(state: AgentState):
    profile = state["athlete_profile"]
    macro_plan = state["macro_plan"]

    meso_plan = []

    # Build microcycle stubs
    for stub in macro_plan.mesocycle_stubs:
        reasoning_messages = [
            SystemMessage(prompts.MESO_REASONING_PROMPT),
            HumanMessage(f"""
                Athlete profile: {profile}
                Macro Plan: {macro_plan}

                Please build a detailed mesocycle plan for this mesocycle stub:
                Phase: {stub.phase}
                Number of weeks: {stub.num_weeks}
                Focus: {stub.focus}
                Start Date: {stub.start_date}
                End Date: {stub.end_date}
            """
            )
        ]
    
        meso_proposal = reasoning_llm.invoke(reasoning_messages)
        
        structured_messages = [
            SystemMessage(prompts.MESO_SUMMARIZER_PROMPT),
                HumanMessage(f"""
                    Convert this plan to structured output.
                    There MUST be exactly {stub.num_weeks} microcycle stubs — one per week.
                    
                    {meso_proposal.content}
                """)
        ]

        MAX_RETRIES = 3
        last_err = None
        
        for i in range(MAX_RETRIES):
            try:
                structured_plan = meso_fortmatter.invoke(structured_messages)
                if structured_plan:
                    break
            except Exception as e:
                print(f"Exception on attempt {i + 1}: {type(e).__name__}: {e}")
                last_err = str(e)
                structured_messages.append(HumanMessage(f"Your response failed validation: {last_err}. Please fix it."))
        if structured_plan is None:
            return {"meso_plans": None, "error": f"meso_agent failed on phase: '{stub.phase}' after {MAX_RETRIES} attempts: {last_err}" }
        meso_plan.append(structured_plan)

    return {"meso_plan": meso_plan, "error": None}


def micro_agent(state: AgentState):
    profile = state['athlete_profile']
    meso_cycles = state['meso_plan']

    micro_plan = []
    
    for meso in meso_cycles:
        for stub in meso.micro_cycle_stubs:
            week_stubs = []

            for i in range(stub.num_swims):
                messages = [
                    SystemMessage(prompts.MICRO_PROMPT),
                    HumanMessage(f"""
                        Strokes to target: {profile.swimData.events}
                        Weekly focus: {stub.focus}


                        You are generating workout stub {i + 1} of {stub.num_swims} for this week.
                        Already planned this week: {week_stubs}

                        Target around (this is not a hard limit): {stub.target_yardage // stub.num_swims} 
                        yards for this workout. Keep in mind this is a workout for just a single day, not the entire week.
                    """)
                ]

                MAX_RETRIES = 3
                last_err = None
                workout_stub = None

                for attempt in range(MAX_RETRIES):
                    try:
                        workout_stub = micro_llm.invoke(messages)
                        if workout_stub:
                            break
                    except Exception as e:
                        print(f"Attempt {attempt + 1} failed: {type(e).__name__}: {e}")
                        last_err = str(e)
                        messages.append(
                            HumanMessage(f"Your response failed validation: {last_err}. Please fix it.")
                        )

                if workout_stub is None:
                    return {
                        "micro_plans": None,
                        "error": f"micro_agent failed on week '{stub.start_date}' swim {i + 1} after {MAX_RETRIES} attempts: {last_err}"
                    }
                week_stubs.append(workout_stub)
                micro_plan.append(workout_stub)

    return {"micro_plan": micro_plan, "error": None}

def orchestrator_agent(state: AgentState):
    macro_result = macro_agent(state)
    if macro_result.get("error"):
        return {"error": macro_result["error"]}

    state["macro_plan"] = macro_result["macro_plan"]

    meso_result = meso_agent(state)
    if meso_result.get("error"):
        return {"error": meso_result["error"]}

    state["meso_plan"] = meso_result["meso_plan"]

    micro_result = micro_agent(state)
    if micro_result.get("error"):
        return {"error": micro_result["error"]}

    return {
        "macro_plan": state["macro_plan"],
        "meso_plan": state["meso_plan"],
        "micro_plan": micro_result["micro_plan"],
        "error": None
    }