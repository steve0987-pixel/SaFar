"""
Pydantic schemas for Smart Trip Copilot.
Defines structured data models for trip requests, POI, routes, and verification.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import date, time


class TripPace(str, Enum):
    RELAXED = "relaxed"
    MODERATE = "moderate"
    INTENSIVE = "intensive"


class BudgetStyle(str, Enum):
    BUDGET = "budget"
    MODERATE = "moderate"
    COMFORT = "comfort"


class PhysicalLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# ==================== INPUT SCHEMAS ====================

class TripRequest(BaseModel):
    """Structured trip request parsed from user input."""
    
    city: str = Field(default="Samarkand", description="Destination city")
    duration_days: int = Field(..., ge=1, le=14, description="Trip duration in days")
    budget_usd: float = Field(..., ge=10, description="Total budget in USD")
    
    interests: List[str] = Field(
        default_factory=list,
        description="User interests: history, nature, food, architecture, etc."
    )
    
    constraints: List[str] = Field(
        default_factory=list,
        description="Specific constraints like 'mountains on day 2'"
    )
    
    start_date: Optional[date] = Field(default=None, description="Trip start date")
    travelers_count: int = Field(default=1, ge=1, description="Number of travelers")
    
    pace: TripPace = Field(default=TripPace.MODERATE, description="Desired trip pace")
    budget_style: BudgetStyle = Field(default=BudgetStyle.MODERATE)
    physical_level: PhysicalLevel = Field(default=PhysicalLevel.MODERATE)
    
    must_visit: List[str] = Field(
        default_factory=list,
        description="POI IDs that must be included"
    )
    
    avoid: List[str] = Field(
        default_factory=list,
        description="POI IDs or categories to avoid"
    )
    
    language: str = Field(default="ru", description="Preferred language: ru, en, uz")


class TripRequestPatch(BaseModel):
    """Partial update to an existing TripRequest."""
    
    duration_days: Optional[int] = None
    budget_usd: Optional[float] = None
    interests: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    start_date: Optional[date] = None
    pace: Optional[TripPace] = None
    # Add more fields as needed


# ==================== POI & ROUTE SCHEMAS ====================

class Coordinates(BaseModel):
    lat: float
    lng: float


class POI(BaseModel):
    """Point of Interest."""
    
    id: str
    name: str
    name_en: Optional[str] = None
    category: List[str]
    description: str
    
    cost_usd: float = 0
    duration_hours: float
    best_time: str = "any"
    opening_hours: Optional[str] = None
    
    district: str = ""
    coordinates: Optional[Coordinates] = None
    
    tags: List[str] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list)
    
    physical_level: PhysicalLevel = PhysicalLevel.LOW
    requirements: List[str] = Field(default_factory=list)


class ActivitySlot(BaseModel):
    """Single activity in an itinerary."""
    
    poi_id: str
    poi_name: str
    start_time: str  # "09:00"
    end_time: str    # "10:30"
    cost_usd: float
    notes: Optional[str] = None


class DayPlan(BaseModel):
    """Plan for a single day."""
    
    day: int
    date: Optional[date] = None
    theme: str
    activities: List[ActivitySlot]
    total_cost: float = 0
    total_hours: float = 0
    notes: Optional[str] = None


class Route(BaseModel):
    """Complete trip route/itinerary."""
    
    id: str
    name: str
    description: str
    
    duration_days: int
    total_cost_usd: float
    style: BudgetStyle
    
    days: List[DayPlan]
    
    highlights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ==================== VERIFICATION SCHEMAS ====================

class CheckResult(BaseModel):
    """Result of a single verification check."""
    
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class VerifierReport(BaseModel):
    """Complete verification report for a route."""
    
    is_feasible: bool
    overall_score: float = Field(ge=0, le=1)
    
    budget_check: CheckResult
    time_check: CheckResult
    constraints_check: CheckResult
    physical_check: CheckResult
    
    issues: List[str] = Field(default_factory=list)
    auto_fixes: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# ==================== USER PROFILE ====================

class UserProfile(BaseModel):
    """User preferences and history."""
    
    user_id: str
    language: str = "ru"
    
    preferences: Dict[str, Any] = Field(default_factory=dict)
    interests_history: List[str] = Field(default_factory=list)
    
    past_trips: List[str] = Field(default_factory=list)  # Route IDs
    favorite_pois: List[str] = Field(default_factory=list)
    
    default_pace: TripPace = TripPace.MODERATE
    default_budget_style: BudgetStyle = BudgetStyle.MODERATE


# ==================== RAG SCHEMAS ====================

class RetrievalResult(BaseModel):
    """Result from RAG retrieval."""
    
    poi: POI
    score: float
    matched_tags: List[str] = Field(default_factory=list)


class Evidence(BaseModel):
    """Evidence used in route planning."""
    
    poi_ids: List[str]
    tips_used: List[str]
    route_template_id: Optional[str] = None


# ==================== RESTAURANT & HOTEL SCHEMAS ====================

class Restaurant(BaseModel):
    """Restaurant data model."""
    
    id: str
    name: str
    name_uz: Optional[str] = None
    category: str  # fine-dining, traditional, casual, cafe, etc.
    cuisine: List[str]  # uzbek, european, korean, etc.
    
    description: str
    description_uz: Optional[str] = None
    
    price_range: str  # $, $$, $$$, $$$$
    avg_check_usd: float
    rating: float = Field(ge=0, le=5)
    reviews_count: int = 0
    
    coordinates: Optional[Coordinates] = None
    address: str = ""
    phone: Optional[str] = None
    opening_hours: str = ""
    
    features: List[str] = Field(default_factory=list)  # wifi, terrace, live-music, etc.
    specialties: List[str] = Field(default_factory=list)
    
    image_url: Optional[str] = None
    booking_required: bool = False
    accepts_cards: bool = True


class Hotel(BaseModel):
    """Hotel data model."""
    
    id: str
    name: str
    name_uz: Optional[str] = None
    stars: int = Field(ge=1, le=5)
    category: str  # luxury, boutique, comfort, standard, budget, guesthouse
    
    description: str
    description_uz: Optional[str] = None
    
    price_per_night_usd: float
    rating: float = Field(ge=0, le=5)
    reviews_count: int = 0
    
    coordinates: Optional[Coordinates] = None
    address: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    
    amenities: List[str] = Field(default_factory=list)  # wifi, pool, spa, gym, etc.
    room_types: List[str] = Field(default_factory=list)
    
    breakfast_included: bool = False
    check_in: str = "14:00"
    check_out: str = "12:00"
    
    image_url: Optional[str] = None
    gallery: List[str] = Field(default_factory=list)


class HotelSearchResult(BaseModel):
    """Result from hotel search."""
    hotel: Hotel
    score: float
    price_match: bool = True


class RestaurantSearchResult(BaseModel):
    """Result from restaurant search."""
    restaurant: Restaurant
    score: float
    cuisine_match: bool = True


# ==================== TRIP PLANNER SCHEMAS (Step 3) ====================

class PlanBlockType(str, Enum):
    """Type of activity block in a plan."""
    POI = "poi"
    MEAL = "meal"
    TRANSIT = "transit"
    FREE = "free"


class PlanBlock(BaseModel):
    """Single block in a day's itinerary."""
    
    start: str  # "09:00"
    end: str    # "11:00"
    type: PlanBlockType
    
    poi_id: Optional[str] = None      # for type=poi
    venue_id: Optional[str] = None    # for type=meal (restaurant id)
    
    name: str = ""                    # Display name
    reason: str = ""                  # "Best morning light for photos"
    cost_usd: float = 0


class PlanDay(BaseModel):
    """Plan for a single day."""
    
    day_number: int
    date: Optional[str] = None        # "2026-02-10"
    theme: str = ""                   # "День 1: Сердце Самарканда"
    blocks: List[PlanBlock] = Field(default_factory=list)


class PlanResponse(BaseModel):
    """Complete trip plan response - frozen contract."""
    
    days: List[PlanDay]
    warnings: List[str] = Field(default_factory=list)
    total_cost_usd: float = 0
    pace: str = "medium"
    poi_count: int = 0
    meal_count: int = 0


class PlanRequest(BaseModel):
    """Request for trip plan generation."""
    
    days: int = Field(default=3, ge=1, le=14, description="Number of days")
    interests: List[str] = Field(
        default_factory=lambda: ["history", "food"],
        description="User interests"
    )
    budget: float = Field(default=100.0, ge=10, description="Budget in USD")
    pace: str = Field(
        default="medium", 
        description="Trip pace: slow (2-3 POI/day), medium (3-4), fast (5-6)"
    )
    start_date: Optional[str] = None  # "2026-02-10"
