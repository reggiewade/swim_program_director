# run_test.py
from lib.agents import macro_agent
from lib.graph import app
from lib.state import AgentState, AthleteProfile, Vitals, SkillLevel, StrengthKPIs, SwimData, Meet

state = AgentState(
    athlete_profile=AthleteProfile(
        vitals=Vitals(age="17", height="6'1"),
        skillLevel=SkillLevel.ELITE,
        kpis=StrengthKPIs(
            backsquat="225", deadlift="275", benchpress="185",
            powerclean="155", snatch="115", verticalleap="28"
        ),
        swimData=SwimData(
            events=["500 Freestyle", "200 Freestyle"],
            times={"50 Freestyle": "23.04", "100 Freestyle": "50.41"}
        ),
        meets=[Meet(name="State Championships", date="2026-02-15")],
        agentNotes="Focus on aerobic base this cycle."
    ),
    macro_plan=None,
    meso_plan=[],
    micro_plan=[],
    daily_workouts=[],
    error=None
)

for step in app.stream(state):
    print(step)