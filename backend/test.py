import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from lib.state import (
    AgentState, AthleteProfile, Vitals, SkillLevel, StrengthKPIs,
    SwimData, Meet, MacroCycle, MesoCycleStub, PhaseType, FocusType
)
from lib.agents import meso_agent, micro_agent

load_dotenv()

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
    macro_plan=MacroCycle(
        cycle_start_date="2025-09-01",
        target_meet=Meet(name="State Championships", date="2026-02-15"),
        mesocycle_stubs=[
            MesoCycleStub(
                phase=PhaseType.GPP,
                num_weeks=6,
                focus=FocusType.AEROBIC,
                start_date="2025-09-01"
            )
        ]
    ),
    meso_plan=[],
    micro_plan=[],
    daily_workouts=[],
)

# ── Run agent ──────────────────────────────────────────────────────────────────
print("\n--- Running Meso Agent ---")
result = meso_agent(fake_state)

if result["error"]:
    print(f"{result['error']}")
    sys.exit(1)

# ── Print results ──────────────────────────────────────────────────────────────
print(f"\nGenerated {len(result['meso_plan'])} mesocycle(s)\n")

for i, meso in enumerate(result["meso_plan"]):
    print(f"Mesocycle {i + 1}:")
    print(f"  Micro Cycle Stubs: {len(meso.micro_cycle_stubs)}")
    for j, stub in enumerate(meso.micro_cycle_stubs):
        print(f"\n  Week {j + 1}:")
        print(f"    Focus:           {stub.focus}")
        print(f"    Target Yardage:  {stub.target_yardage}")
        print(f"    Num Swims:       {stub.num_swims}")
        print(f"    Weight Sessions: {stub.weight_room_sessions}")
        print(f"    Start Date:      {stub.start_date}")
        print(f"    End Date:        {stub.end_date}")

# ── Run Micro Agent ────────────────────────────────────────────────────────────
fake_state["meso_plan"] = result["meso_plan"]

print("\n--- Running Micro Agent ---")
micro_result = micro_agent(fake_state)

if micro_result["error"]:
    print(f"{micro_result['error']}")
    sys.exit(1)

print(f"\nGenerated {len(micro_result['micro_plan'])} workout stubs\n")

i = 1
for stub in micro_result["micro_plan"]:
    print(f"  Day {i}: {stub.focus} | {stub.stroke_focus} | {stub.target_yardage}y")
    i+=1