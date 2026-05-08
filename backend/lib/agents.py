from dotenv import load_dotenv

from langchain_core.messages import SystemMessage, HumanMessage
import lib.state as state
import lib.prompts as prompts
from lib.state import AgentState, Workout, get_yardage_ceiling
import lib.chatlib as chatlib
from lib.rag import retrieve_workouts
from datetime import date

load_dotenv()

reasoning_llm = chatlib.get_chat_model("BSU_").llm      # claude
macro_formatter = chatlib.get_chat_model("API_").llm.with_structured_output(state.MacroCycle)       # gemma4
meso_fortmatter = chatlib.get_chat_model("API_").llm.with_structured_output(state.MesoCycle)
micro_llm = chatlib.get_chat_model("API_").llm.with_structured_output(state.WorkoutStub)
workout_llm = chatlib.get_chat_model("API_").llm.with_structured_output(state.Workout)


def macro_agent(state: AgentState) -> dict:

    profile = state["athlete_profile"]

    reasoning_messages = [
        SystemMessage(prompts.MACRO_REASONING_PROMPT),
        HumanMessage(f"""
            Please build a macro training cycle for this athlete:
            Athlete Profile: {profile}
            The start date is: {date.today().isoformat()}
        """
        )
    ]

    macro_proposal = reasoning_llm.invoke(reasoning_messages)
    structured_messages = [
        SystemMessage(prompts.MACRO_SUMMARIZER_PROMPT),
        HumanMessage(macro_proposal.content)
    ]
    MAX_RETRIES = 3
    last_err = None

    for attempt in range(MAX_RETRIES):
        try:
            structured_plan = macro_formatter.invoke(structured_messages)
            if structured_plan:
                print(f"""Generated MacroCycle: {structured_plan}\n\n""")
                return {"macro_plan": structured_plan, "error": None}

        except Exception as e:
            print(f"Exception on attempt {attempt + 1}: {type(e).__name__}: {e}")
            last_err = str(e)
            structured_messages.append(HumanMessage(f"Your response failed validation: {last_err}. Please fix it."))

    print(f"All retries exhausted. Last error: {last_err}")
    return {"macro_plan": None, "error" : f"macro_agent failed after {MAX_RETRIES} attempts: {last_err}"}

def meso_agent(state: AgentState):
    profile = state["athlete_profile"]
    macro_plan = state["macro_plan"]

    meso_plan = []

    for stub in macro_plan.mesocycle_stubs:
        yardage_ceiling = get_yardage_ceiling(int(profile.vitals.age), stub.focus, stub.phase)

        reasoning_messages = [
            SystemMessage(prompts.MESO_REASONING_PROMPT),
            HumanMessage(f"""
                Athlete profile: {profile}
                Macro Plan: {macro_plan}

                Please build a detailed mesocycle plan for this mesocycle stub:
                Phase: {stub.phase}
                Number of weeks: {stub.num_weeks}
                Focus: {stub.focus}
                MAXIMUM Yardage (per week): {yardage_ceiling} (based on age, phase and focus)
                You can adjust the weekly yardage as needed, but it should not exceed the ceiling.
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
                    print(f"""Generated MesoCycle for phase {stub.phase}: {structured_plan}\n\n""")
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
                        Already planned this week: {week_stubs} PLEASE think about possible variations in 
                        strokes week to week to ensure variety.

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
                        print(f"""Generated WorkoutStub for week starting {stub.start_date}, swim {i + 1}: {workout_stub}\n\n""")
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

def workout_generator_agent(workout_stub: state.WorkoutStub) -> Workout:
    MAX_RETRIES = 3
    rag_query = (
        f"{workout_stub.focus.value} "
        f"{workout_stub.phase.value} "
        f"{workout_stub.stroke_focus.value} "
        f"workout "
        f"{workout_stub.target_yardage} yards"
    )
    try:
        docs = retrieve_workouts(query=rag_query, k=3)
        print(f"Retrieved {len(docs)} docs")
        retrieved = "\n\n".join([doc.page_content for doc in docs])
        
        feedback = ""

        for attempt in range(MAX_RETRIES):
            prompt = f"""
            You are an expert swim coach. Using the following reference workouts, 
            generate a new {workout_stub.focus.value} {workout_stub.phase.value} {workout_stub.stroke_focus.value} 
            workout targeting {workout_stub.target_yardage} yards.
            Generate sets to hit that target, then leave total_yardage blank. 
            It will be computed separately.

            The generated workout MUST be within 5% of target yardage.
            {feedback}

            Reference workouts:
            {retrieved}

            Generate a new workout in the same format as the references above.
            ONLY output the workout.  DON'T Provide anything else.
            """

            res = workout_llm.invoke(prompt)
            tolerance = 0.05 * workout_stub.target_yardage
            
            if abs(res.total_yardage - workout_stub.target_yardage) <= tolerance:
                return res
            else:
                diff = res.total_yardage - workout_stub.target_yardage
                if diff > 0:
                    feedback = (
                        f"The previous workout was TOO SHORT by {diff} yards. "
                        f"Increase volume."
                    )
                else:
                    feedback = (
                        f"The previous workout was TOO LONG by {-diff} yards. "
                        f"Decrease volume."
                    )
        return res
    except Exception as e:
        print(f"workout_generator_agent failed: {type(e).__name__}: {e}")
        return None

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