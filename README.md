# Swim Program Director

This program generates a plan leading up to a specified meet for swimmers.  This generates
the Macro, Meso and Micro cycles along with the ability to generate personalized swim sets
based on the output of those cycles.

## Description

This project is based on the classic athlete phase planner where the main phases are: GPP, SPP,
Taper, and De load.  GPP being the general strength preparation phase, SPP being the specialized
preparation phase, Taper being the phase right before the major meet, and De Load being the phase
right after a heavy GPP or meet.  The architecture of this project is as follows; orchestrator ->
macro_agent -> orchestrator -> meso_agent -> orchestrator -> micro_agent.  With all of the micro
cycles planned, the future plans of this project will be to allow the user to open the web app
and be given the option to generate the workout for the specific day.  The original plan for this
project was to have the agent generate all the workouts at once given the workout_stubs, however
this would not be cost effective at all.

## Getting Started

### API Keys

Look in .example.env for the format to populate API keys.  You will need keys for 
two different models, it is recommended that the most powerful model be used for the
reasoner and the weaker model for the formatter.

### Dependencies

You must install the following python modules:
```bash
pip install langchain_core
pip install langchain_ollama
pip install langchain_chroma
pip install flask
pip install flask_cors
```
Via the frontend folder, run:
```bash
rm package.json package-lock.json -rf node_modules
npm init
```
This will delete all the npm dependencies and initialize a fresh package.json

### Executing program
Change directories to the backend lib folder and run ingest.py to populate the vector
database.
```bash
cd backend/lib
python3 ingest.py
```

Change directories back to the backend and run the server
```bash
cd backend
python3 server.py
```

Change directories to the frontend folder and run the npm server
```bash
cd ../
cd frontend
npm run dev
```

Navigate to http://localhost:3000/ to open the frontend UI for the web app.  Fill
out the form and click "Generate Training Plan."  This will send a request to the 
flask app, however the frontend is not developed so it won't redirect to another page.
This will be implemented later.  All logs will be displayed in the python server.

#### Generating Workouts
As of right now there is no frontend to generate workouts, however you can generate workouts via
workout_generator.py.  Unfortunately, you will need to edit the object manually as, again, there is
no frontend to support the feature yet.  This workout agent will generate a set based on the constraints
the use gives it and eventually will just grab the workoutstub when they are dumped into a database.


### What was AI used for?
I used AI in this project for some of the questions I had regarding design of the architecture and
as a debugger for certain pydantic issues I was facing, as well as refactoring some of the reasoning
prompts to make them more concise for the LLMs using them.  I also did have AI write a template for
my frontend as I didn't have the time to design a nice web page UI (I probably should've stuck to 
a terminal based program for the time being but oh well.)