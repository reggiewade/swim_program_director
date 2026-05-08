from flask import Flask, request, jsonify
from flask_cors import CORS
from lib.graph import app as langgraph_app
from lib.state import AgentState, AthleteProfile, Vitals, SkillLevel, StrengthKPIs, SwimData

flask_app = Flask(__name__)
CORS(flask_app)

# Flask endpoint to recieve athlete data and run the agent.
# The agent will process the data and generate a swim training plan
# based on the athlete profile, vitals, KPIs and swim data provided in the request payload.

@flask_app.route("/run", methods=["POST"])
def run_agent():
    req = request.get_json()
    print("Received payload:", req)

    vitals = req["vitals"]
    kpis = req["kpis"]
    swim = req["swimData"]

    state = AgentState(
        athlete_profile=AthleteProfile(
            vitals=Vitals(age=vitals["age"], height=vitals["height"]),
            skillLevel=SkillLevel(req["skillLevel"]),
            kpis=StrengthKPIs(
                backsquat=kpis["backsquat"],
                deadlift=kpis["deadlift"],
                benchpress=kpis["benchpress"],
                powerclean=kpis["powerclean"],
                snatch=kpis["snatch"],
                verticalleap=kpis["verticalleap"],
            ),
            swimData=SwimData(events=swim["events"], times=swim["times"]),
            meets=[],
            agentNotes=req.get("agentNotes", ""),
        ),
        macro_plan=None, meso_plan=[], micro_plan=[], daily_workouts=[],
    )

    langgraph_app.invoke(state)

if __name__ == "__main__":
    flask_app.run(debug=True, port=8000)