
from lib.state import FocusType, PhaseType, StrokeFocus, Workout, WorkoutStub
from lib.agents import workout_generator_agent


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

temp_stub = WorkoutStub(
    phase=PhaseType.TAPER,
    focus=FocusType.POWER,
    stroke_focus=StrokeFocus.FREESTYLE,
    target_yardage=1500
)

res = workout_generator_agent(temp_stub)
print_workout(res)