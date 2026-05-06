import chatlib
from dotenv import load_dotenv
from rag import retrieve_workouts
from state import Workout

load_dotenv()

llm = chatlib.get_chat_model("API_").llm.with_structured_output(Workout)        # Restrict to a Workout output

query = "Power Taper Freestyle workout 1500 yards"
docs = retrieve_workouts(query=query, k=3)
retrieved = "\n\n".join([doc.page_content for doc in docs])

def print_workout(workout: Workout) -> None:
    print(f"Phase:        {workout.phase}")
    print(f"Focus:        {workout.focus}")
    print(f"Stroke Focus: {workout.stroke_focus}")
    print(f"Total Yards:  {workout.total_yardage}")
    print()

    for section in workout.sections:
        print(f"{section.name} ({section.yardage}y):")
        for item in section.items:
            interval = f" @ {item.interval}" if item.interval else ""
            print(f"  {item.reps}x{item.distance}{interval} — {item.description} ({item.yardage}y)")
        print()

prompt = f"""
You are an expert swim coach. Using the following reference workouts, 
generate a new Power Taper Freestyle workout targeting 1500 yards.
Generate sets to hit that target, then leave total_yardage blank. 
It will be computed separately.

Reference workouts:
{retrieved}

Generate a new workout in the same format as the references above.
ONLY output the workout.  DONT Provide anything else.
"""

res = llm.invoke(prompt)
print_workout(res)