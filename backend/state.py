from langchain_core.messages import AnyMessage
from typing import Annotated, Dict, TypedDict, List
from proto import Enum
from pydantic import BaseModel, Field, field_validator
import operator

class PhaseType(str, Enum):
    GPP = "GPP"                 # General Physical Preparation
    SPP = "SPP"                 # Specific Physical Preparation
    TAPER = "TAPER"             # Taper Phase
    DE_LOAD = "DE_LOAD"         # De-Load/Recovery Phase
    
class FocusType(str, Enum):
    AEROBIC = "Aerobic"
    ANAEROBIC = "Anaerobic"
    TECHNIQUE = "Technique"
    POWER = "Power"
    RECOVERY = "Recovery"
    
class Vitals(BaseModel):
    age: str
    height: str
    weight: str

class StrengthKPIs(BaseModel):
    backsquat: str
    deadlift: str
    benchpress: str
    powerclean: str
    snatch: str
    verticalleap: str

class SwimData(BaseModel):
    events: List[str]
    times: Dict[str, str]

class Meet(BaseModel):
    name: str
    date: str

class AthleteProfile(BaseModel):
    vitals: Vitals
    kpis: StrengthKPIs
    swimData: SwimData
    meets: List[Meet]
    agentNotes: str
    

class AgentState(TypedDict):
    
    # Messages from the user and agent's response
    messages: Annotated[List[AnyMessage], operator.add]
    
    # 1 Athlete Profile
    athlete_profile: dict
    
    # 2 Macro/Meso/Micro Plan
    macro_plan: dict            # Big picture plan for the entire training cycle
    meso_plan: List[dict]       # More detailed plan for a specific training block (e.g., 4 weeks)
    micro_plan: List[dict]      # Very detailed plan for a specific week
    daily_workouts: List[dict]  # Workouts for each day of the week
    
    # 4. Routing & Validation Flags
    # Helps the Orchestrator decide if it needs to loop back
    is_profile_complete: bool
    validation_errors: List[str]
    current_phase: PhaseType
    
class MicroPlan(BaseModel):
    week_number: int
    total_weekly_yardage: int = Field(gt=0, description="Total yardage for the week")
    focus: FocusType = Field(description="Focus of the week")
    
    @field_validator('total_weekly_yardage')
    def validate_yardage(cls, v):
        if v > 40000:
            raise ValueError("Yardage exceeds reasonable limits for a week.")
        return v

class MesoCycle(BaseModel):
    phase: PhaseType
    num_weeks: int = Field(
        gt=0, 
        description="""
            GPP: General Physical Preparation (6-8 week build with peak effort starting around week 4-5). Focus
            on building aerobic base, general strength, and work capacity.  Volume is high with intensity 
            starting low and gradually increasing.
            SPP: Specific Physical Preparation (5-6 week with effort ranging from moderate to high).  Focus
            on developing event-specific fitness (e.g. anaerobic for sprinters, aerobic for distance swimmers) and
            refining technique.  Volume is moderate to high with intensity peaking in week 5-6.
            TAPER: Taper Phase (1-2 weeks with race pace training and 40-60% volume reduction). Focus on maintaining
            or increasing intensity while increasing recovery time.
            DE_LOAD: De-Load/Recovery Phase (Usually 1 week with an emphasis on strength and conditioning).  This is 
            a recovery phase to allow the body to adapt and prevent injury. Volume and intensity are low.
        """)
    focus: FocusType = Field(
        description="""
            AEROBIC: Foundational capacity building, EN1-EN2 zones, short to moderate intervals, high volume.
            ANAEROBIC: Lactate tolerance, EN3-SP1 zones, longer intervals, moderate volume.
            POWER: Explosive strength, SP2-SP3 zones, very short distance (15-25m) with full recovery.
            TECHNIQUE: Stroke mechanics, starts, turns, drills, and neuromuscular efficiency.
            RECOVERY: Active recovery to flush lactate and restore CNS
            """)
    target_weekly_yardage: int = Field(gt=0, description="Target weekly yardage for the mesocycle")
    weight_room_sessions_per_week: int = Field(ge=0, description="Number of weight room sessions per week")
    
    # TODO: figure out a way to the yardage and weight room sessions based on athletes profile and goals
    @field_validator('num_weeks')
    def validate_num_weeks(cls, v):
        if v > 12:
            raise ValueError("Meso cycle cannot be longer than 12 weeks.")
        return v
    
    @field_validator('target_weekly_yardage')
    def validate_yardage(cls, v):
        if v > 40000:
            raise ValueError("Yardage exceeds reasonable limits for a week.")
        return v
    
    @field_validator('weight_room_sessions_per_week')
    def validate_weight_room_sessions(cls, v):
        if v > 4:
            raise ValueError("Weight room sessions per week cannot exceed 4.")
        return v