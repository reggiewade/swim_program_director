from langchain_core.messages import AnyMessage
from typing import Annotated, Dict, TypedDict, List
from proto import Enum
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
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
    
class SkillLevel(str, Enum):
    RECREATIONAL = "Recreational"
    DEVELOPMENTAL = "Developmental"
    COMPETITIVE = "Competitive"
    ELITE = "Elite"
    
SKILL_VOLUME_MULTIPLIERS = {
    SkillLevel.RECREATIONAL: 0.50,
    SkillLevel.DEVELOPMENTAL: 0.70,
    SkillLevel.COMPETITIVE: 0.90,
    SkillLevel.ELITE: 1.00
}

def get_yard_progression_rate(skill_level: SkillLevel) -> float:
    return {
        SkillLevel.RECREATIONAL:  1.05,
        SkillLevel.DEVELOPMENTAL: 1.08,
        SkillLevel.COMPETITIVE:   1.10,
        SkillLevel.ELITE:         1.15,
    }.get(skill_level, 1.0)

# Helper Functions & Constants
def get_age_yardage_ceiling(age: int) -> int:
    """Returns max weekly yardage based on swimmer age."""
    if age <= 10:   return 15000
    if age <= 12:   return 25000
    if age <= 14:   return 35000
    if age <= 18:   return 55000
    if age <= 25:   return 80000
    return 40000  #25+

def get_intensity_volume_multiplier(focus: FocusType) -> float:
    """High intensity = lower volume ceiling."""
    return {
        FocusType.RECOVERY:   1.0,
        FocusType.AEROBIC:    1.0,
        FocusType.TECHNIQUE:  0.9,
        FocusType.ANAEROBIC:  0.75,
        FocusType.POWER:      0.55,
    }.get(focus, 1.0)
    
def get_phase_volume_multiplier(phase: PhaseType) -> float:
    """Taper and de-load phases require volume reduction."""
    return {
        PhaseType.GPP:     1.0,
        PhaseType.SPP:     0.85,
        PhaseType.TAPER:   0.50,
        PhaseType.DE_LOAD: 0.40,
    }.get(phase, 1.0)
    
def get_max_weight_room_sessions(phase: PhaseType, focus: FocusType, skill_level: SkillLevel, age_ceiling: int, current_yardage: int) -> int:
    base_sessions = {
        SkillLevel.RECREATIONAL: 2,
        SkillLevel.DEVELOPMENTAL: 3,
        SkillLevel.COMPETITIVE: 4,
        SkillLevel.ELITE: 5,
    }.get(skill_level, 2)
    
    phase_modifier = {
        PhaseType.GPP:     0,  
        PhaseType.SPP:    -1,  
        PhaseType.TAPER:  -2,  
        PhaseType.DE_LOAD:-2,  
    }.get(phase, 0)

    focus_modifier = {
        FocusType.RECOVERY:  -2,
        FocusType.AEROBIC:    0,
        FocusType.TECHNIQUE:  0,
        FocusType.ANAEROBIC: -1,
        FocusType.POWER:     -1,
    }.get(focus, 0)
    
    load_ratio = current_yardage / age_ceiling
    load_penalty = 0
    if load_ratio > 0.85:
        load_penalty = -1

    calculated = base_sessions + phase_modifier + focus_modifier + load_penalty
    
    # Taper phase requires at least 1 session
    if skill_level in [SkillLevel.COMPETITIVE, SkillLevel.ELITE] and phase == PhaseType.TAPER:
        return max(1, calculated)
        
    return max(0, calculated)
    
class Vitals(BaseModel):
    age: str
    height: str

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
    
    # Extensive safety checks to ensure safe training for all ages
    @model_validator(mode="after")
    def validate_yardage(self, info: ValidationInfo):
        ctx = info.context
        athlete_age = ctx.get("athlete_age")
        last_week_yardage = ctx.get("last_week_yardage")
        
        age_ceiling = get_age_yardage_ceiling(athlete_age)
        
        intensity_multi = get_intensity_volume_multiplier(self.focus)
        phase_multi = get_phase_volume_multiplier(self.phase)
        
        adjusted_ceil = int(age_ceiling * intensity_multi * phase_multi)
        
        if self.target_weekly_yardage > adjusted_ceil:
            raise ValueError(
                f"Yardage {self.target_weekly_yardage:,} exceeds safe limit of "
                f"{adjusted_ceil:,} for age {athlete_age}, "
                f"phase={self.phase}, focus={self.focus}."
            )
        if self.target_weekly_yardage:
            max_increase = int(get_yard_progression_rate(self.focus) * last_week_yardage)
            
            if self.target_weekly_yardage > last_week_yardage + max_increase:
                raise ValueError(
                    f"Yardage {self.target_weekly_yardage:,} exceeds safe limit of "
                    f"{last_week_yardage + max_increase:,} for age {athlete_age}, "
                    f"phase={self.phase}, focus={self.focus}."
                )
                
        max_allowed = get_max_weight_room_sessions(self.phase, self.focus, self.focus, age_ceiling, last_week_yardage)
        if self.weight_room_sessions_per_week > max_allowed:
            raise ValueError(
                f"Weight sessions ({self.weight_room_sessions_per_week}) exceed the "
                f"maximum of {max_allowed} for {self.phase} phase at this yardage load."
        )