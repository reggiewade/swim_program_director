from lib.graph import app
from lib.state import AgentState, AthleteProfile, Meet, Vitals, SkillLevel, StrengthKPIs, SwimData

def main():
    fake_state = AgentState(
        athlete_profile=AthleteProfile(
            vitals=Vitals(age="17", height="6'1"),
            skillLevel=SkillLevel.ELITE,
            kpis=StrengthKPIs(
                backsquat="225", deadlift="275", benchpress="185",
                powerclean="155", snatch="115", verticalleap="28"
            ),
            swimData=SwimData(
                events=["50 Freestyle", "100 Butterfly"],
                times={"50 Freestyle": "23.04", "100 Butterfly": "55.07"}
            ),
            meets=[Meet(name="State Championships", date="2026-02-15")],
            agentNotes="Focus on aerobic base this cycle."
        ),
        macro_plan=None,
        meso_plan=[],
        micro_plan=[],
        daily_workouts=[],
    )

    result = app.invoke(fake_state)
    print(result)

if __name__ == "__main__":
    main()