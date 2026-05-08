from typing import Dict, TypedDict, List, Optional
from enum import Enum
import warnings
from typing import Literal
from pydantic import BaseModel, model_validator, field_validator, computed_field
from datetime import datetime, timedelta

class PhaseType(str, Enum):
    GPP = "GPP"                 # General Physical Preparation
    SPP = "SPP"                 # Specific Physical Preparation
    TAPER = "Taper"             # Taper Phase
    DE_LOAD = "De-Load"         # De-Load/Recovery Phase
    
class FocusType(str, Enum):
    AEROBIC = "Aerobic"
    ANAEROBIC = "Anaerobic"
    TECHNIQUE = "Technique"
    TAPER = "Taper"
    POWER = "Power"
    RECOVERY = "Recovery"
    THRESHOLD = "Threshold"

class StrokeFocus(str, Enum):
    BUTTERFLY = "Butterfly"
    FREESTYLE = "Freestyle"
    BREASTSTROKE = "Breaststroke"
    BACKSTROKE = "Backstroke"
    IM = "IM"
    
class SkillLevel(str, Enum):
    RECREATIONAL = "Recreational"
    DEVELOPMENTAL = "Developmental"
    COMPETITIVE = "Competitive"
    ELITE = "Elite"

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

def get_yardage_ceiling(age: int, focus: FocusType, phase: PhaseType) -> int:
    """Gets the adjusted yardage ceiling based on age, focus, and phase for each microcycle (weeks)"""
    base_ceiling = get_age_yardage_ceiling(age)
    intensity_multiplier = get_intensity_volume_multiplier(focus)
    phase_multiplier = get_phase_volume_multiplier(phase)
    
    # calcate adjusted ceiling based on age, focus, and phase
    adjusted_ceiling = int(base_ceiling * intensity_multiplier * phase_multiplier)
        
    return adjusted_ceiling

#  For future development
# def get_max_weight_room_sessions(phase: PhaseType, focus: FocusType, skill_level: SkillLevel, age_ceiling: int, current_yardage: int) -> int:
#     base_sessions = {
#         SkillLevel.RECREATIONAL: 2,
#         SkillLevel.DEVELOPMENTAL: 3,
#         SkillLevel.COMPETITIVE: 4,
#         SkillLevel.ELITE: 5,
#     }.get(skill_level, 2)
    
#     phase_modifier = {
#         PhaseType.GPP:     0,  
#         PhaseType.SPP:    -1,  
#         PhaseType.TAPER:  -2,  
#         PhaseType.DE_LOAD:-2,  
#     }.get(phase, 0)

#     focus_modifier = {
#         FocusType.RECOVERY:  -2,
#         FocusType.AEROBIC:    0,
#         FocusType.TECHNIQUE:  0,
#         FocusType.ANAEROBIC: -1,
#         FocusType.POWER:     -1,
#     }.get(focus, 0)
    
    # load_ratio = current_yardage / age_ceiling
    # load_penalty = 0
    # if load_ratio > 0.85:
    #     load_penalty = -1

    # calculated = base_sessions + phase_modifier + focus_modifier + load_penalty
    
    # # Taper phase requires at least 1 session
    # if skill_level in [SkillLevel.COMPETITIVE, SkillLevel.ELITE] and phase == PhaseType.TAPER:
    #     return max(1, calculated)
        
    # return max(0, calculated)
    
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
    skillLevel: SkillLevel
    kpis: StrengthKPIs
    swimData: SwimData
    meets: List[Meet]
    agentNotes: str
    
class WorkoutItem(BaseModel):
    reps: int
    sets: int
    distance: int
    interval: Optional[str] = None
    description: str

    @computed_field
    @property
    def yardage(self) -> int:
        return self.reps * self.sets * self.distance

class WorkoutSection(BaseModel):
    name: str
    items: list[WorkoutItem]

    @computed_field
    @property
    def yardage(self) -> int:
        return sum(item.yardage for item in self.items)

class Workout(BaseModel):
    phase: str
    focus: str
    stroke_focus: str
    total_yardage: Optional[int] = None
    sections: list[WorkoutSection]

    def model_post_init(self, __context):
        self.total_yardage = sum(section.yardage for section in self.sections)

class WorkoutStub(BaseModel):
    phase: PhaseType
    focus: FocusType
    stroke_focus: StrokeFocus
    target_yardage: int
    
        
class MicroCycleStub(BaseModel):
    focus: FocusType
    target_yardage: int
    weight_room_sessions: int
    num_swims: int
    start_date: str

    @field_validator("start_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")
        return v

    # Add 7 days to the start date
    @computed_field
    @property
    def end_date(self) -> str:
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=6) 
        return end_dt.strftime("%Y-%m-%d")

class MesoCycle(BaseModel):
    micro_cycle_stubs: List[MicroCycleStub]

class MesoCycleStub(BaseModel):
    phase: PhaseType
    num_weeks: int
    focus: FocusType
    start_date: str        # "YYYY-MM-DD"
        
    # Validate date
    @field_validator("start_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")
        return v
        # Give a warning if the mesocycle is unusually long
    @model_validator(mode="after")
    def warn_unusual_duration(self):
        PHASE_WEEK_RANGES = {
            PhaseType.GPP:     (6, 8),
            PhaseType.SPP:     (5, 6),
            PhaseType.TAPER:   (1, 2),
            PhaseType.DE_LOAD: (1, 1),
        }
        min_w, max_w = PHASE_WEEK_RANGES[self.phase]
        if not (min_w <= self.num_weeks <= max_w):
            warnings.warn(
                f"{self.phase} duration of {self.num_weeks} weeks is outside "
                f"the typical {min_w}-{max_w} week range."
            )
        return self

    # Compute end date
    @computed_field 
    @property
    def end_date(self) -> str:
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(weeks=self.num_weeks) - timedelta(days=1)
        return end_dt.strftime("%Y-%m-%d")
    
class MacroCycle(BaseModel):
    cycle_start_date: str
    target_meet: Meet
    mesocycle_stubs: List[MesoCycleStub]
    
class AgentState(TypedDict):
    
    athlete_profile: AthleteProfile
    
    macro_plan: MacroCycle                                      # Big picture plan for the entire training cycle
    meso_plan: List[MesoCycle]                                  # More detailed plan for a specific training block (e.g., 4 weeks)
    micro_plan: List[WorkoutStub]                               # Very detailed plan for a specific week
    daily_workouts: List[Workout]                               # Workouts for each day of the week
    next_agent: str                                             # orchestrator writes this to route
    current_phase: Literal["macro", "meso", "micro", "daily", "done"]
