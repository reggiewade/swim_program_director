from langchain_core.messages import AnyMessage
from typing import Dict, TypedDict, List
from enum import Enum
import warnings
from typing import Annotated, Literal
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, model_validator, ValidationInfo, field_validator, computed_field
from datetime import datetime, timedelta

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
    skillLevel: SkillLevel
    kpis: StrengthKPIs
    swimData: SwimData
    meets: List[Meet]
    agentNotes: str
    
class WorkoutSection(BaseModel):
    name: str
    section_yardage: int
    description: str
    
class DailyWorkout(BaseModel):
    date: str
    focus: FocusType
    total_yardage: int
    sections: List[WorkoutSection]
    
    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")
        return v
    
    @model_validator(mode="after")
    def validate_total_yardage(self):
        calculated_yardage = sum(section.section_yardage for section in self.sections)
        if self.total_yardage != calculated_yardage:
            raise ValueError(
                f"Total yardage {self.total_yardage} does not match "
                f"calculated yardage {calculated_yardage}."
            )
        return self
    
class MicroCycle(BaseModel):
    week_number: int
    phase: PhaseType
    total_weekly_yardage: int = Field(gt=0, description="Total yardage for the week")
    focus: FocusType = Field(description="Focus of the week")
    daily_workouts: List[DailyWorkout]
        
class MicroCycleStub(BaseModel):
    week_number: int
    focus: FocusType
    target_weekly_yardage: int
    start_date: str  # The Monday of the week in YYYY-MM-DD

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
    num_weeks: int
    micro_cycle_stubs: List[MicroCycleStub]
    phase: PhaseType
    focus: FocusType
    target_weekly_yardage: int = Field(gt=0, description="Target weekly yardage for the mesocycle")
    weight_room_sessions_per_week: int = Field(ge=0, description="Number of weight room sessions per week")
    
    # Extensive safety checks to ensure safe training for all ages
    @model_validator(mode="after")
    def validate_yardage(self, info: ValidationInfo):
        ctx = info.context
        athlete_age = ctx.get("athlete_age")
        skill_level = ctx.get("skill_level")
        last_week_yardage = ctx.get("last_week_yardage")
        
        age_ceiling = get_age_yardage_ceiling(athlete_age)
        intensity_multi = get_intensity_volume_multiplier(self.focus)
        phase_multi = get_phase_volume_multiplier(self.phase)
        adjusted_ceil = int(age_ceiling * intensity_multi * phase_multi)

        prev_yardage = last_week_yardage

        for stub in self.micro_cycle_stubs:
            if stub.target_weekly_yardage > adjusted_ceil:
                raise ValueError(
                    f"Week {stub.week_number} yardage {stub.target_weekly_yardage:,} "
                    f"exceeds safe limit of {adjusted_ceil:,} for age {athlete_age}, "
                    f"phase={self.phase}, focus={self.focus}."
                )
            
            max_allowed = int(get_yard_progression_rate(skill_level) * prev_yardage)
            if stub.target_weekly_yardage > max_allowed:
                raise ValueError(
                    f"Week {stub.week_number} yardage {stub.target_weekly_yardage:,} "
                    f"exceeds safe progression limit of {max_allowed:,} "
                    f"from previous week of {prev_yardage:,}."
                )
            prev_yardage = stub.target_weekly_yardage
        return self
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
    @model_validator(mode="after")
    def validate_stub_count(self):
        if len(self.micro_cycle_stubs) != self.num_weeks:
            raise ValueError(
                f"Expected {self.num_weeks} micro cycle stubs, "
                f"got {len(self.micro_cycle_stubs)}."
            )
        return self

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
    mesocycles: List[MesoCycleStub]
    
class AgentState(TypedDict):
    
    athlete_profile: AthleteProfile
    
    macro_plan: MacroCycle                                  # Big picture plan for the entire training cycle
    meso_plan: List[MesoCycle]                              # More detailed plan for a specific training block (e.g., 4 weeks)
    micro_plan: List[MicroCycle]                            # Very detailed plan for a specific week
    daily_workouts: List[DailyWorkout]                      # Workouts for each day of the week
    messages: Annotated[list[AnyMessage], add_messages]     # List of messages
    next_agent: str                                         # orchestrator writes this to route
    current_phase: Literal["macro", "meso", "micro", "daily", "done"]