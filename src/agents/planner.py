"""
AI Route Planner - Generates trip routes using LLM and RAG.
100% AI-powered generation - no hardcoded templates.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import (
    TripRequest, POI, Route, DayPlan, ActivitySlot, 
    BudgetStyle, Evidence, PhysicalLevel
)
from src.rag.retriever import HybridPOIRetriever, TipsRetriever, FilterCriteria
from src.utils.llm import get_llm_client


# System prompt for route generation
ROUTE_PLANNER_SYSTEM = """Ты — эксперт по планированию путешествий в Самарканде, Узбекистан.
Твоя задача — создавать оптимальные маршруты на основе:
- Доступных достопримечательностей (POIs)
- Бюджета и предпочтений туриста
- Логистики (расстояние, время работы, физическая нагрузка)

Правила:
1. Размещай POI логично по географии (близкие места рядом в расписании)
2. Учитывай время работы: большинство мест 08:00-18:00
3. Планируй 4-7 активностей в день для умеренного темпа
4. Для budget стиля — выбирай дешёвые и бесплатные места
5. Оставляй время на обед (12:00-14:00) и отдых
6. Горные туры занимают весь день (07:00-17:00)
7. Шахи-Зинда, Регистан, Гури-Эмир — must-see для первого дня
"""


class AIRoutePlanner:
    """
    AI-powered route planner that:
    1. Uses hybrid RAG to retrieve relevant POIs
    2. Uses LLM to intelligently plan and sequence activities
    3. Generates multiple route variants dynamically
    4. Respects all user constraints
    """
    
    def __init__(
        self,
        poi_retriever: HybridPOIRetriever = None,
        tips_retriever: TipsRetriever = None,
        llm_client = None
    ):
        self.poi_retriever = poi_retriever or HybridPOIRetriever()
        self.tips_retriever = tips_retriever or TipsRetriever()
        self.llm_client = llm_client or get_llm_client()
        print("🤖 AI Route Planner initialized (no templates, 100% AI)")
    
    def generate_routes(
        self,
        trip_request: TripRequest,
        num_variants: int = 3
    ) -> Tuple[List[Route], Evidence]:
        """
        Generate route variants using AI:
        1. Retrieve relevant POIs using RAG
        2. Get contextual tips
        3. Use LLM to generate optimized routes
        
        Returns:
            (list of Routes, Evidence showing what data was used)
        """
        
        # Step 1: Retrieve relevant POIs using hybrid search
        filters = self._build_filters(trip_request)
        relevant_pois = self.poi_retriever.search(
            trip_request=trip_request,
            filters=filters,
            top_k=25
        )
        
        # Step 2: Get mountain POIs if needed
        mountain_pois = []
        mountain_day = self._get_mountain_day(trip_request)
        if mountain_day:
            mountain_pois = self.poi_retriever.get_mountain_options()
            print(f"🏔️ Mountain day: {mountain_day}, options: {len(mountain_pois)}")
        
        # Step 3: Get relevant tips for context
        tips = self.tips_retriever.get_relevant_tips(trip_request)
        
        # Step 4: Generate routes using AI
        available_pois = [r.poi for r in relevant_pois]
        
        routes = []
        styles = ["budget", "balanced", "comfort"][:num_variants]
        
        for style in styles:
            route = self._generate_ai_route(
                trip_request=trip_request,
                pois=available_pois,
                mountain_pois=mountain_pois,
                mountain_day=mountain_day,
                tips=tips,
                style=style
            )
            if route:
                routes.append(route)
        
        # Build evidence
        evidence = Evidence(
            poi_ids=[r.poi.id for r in relevant_pois[:15]],
            tips_used=tips[:5],
            route_template_id=None  # No templates used!
        )
        
        return routes[:num_variants], evidence
    
    def _build_filters(self, request: TripRequest) -> FilterCriteria:
        """Build filter criteria from trip request."""
        return FilterCriteria(
            city=request.city,
            categories=request.interests if request.interests else None,
            max_cost_usd=request.budget_usd / request.duration_days * 0.5,
            physical_level=request.physical_level.value if hasattr(request.physical_level, 'value') else str(request.physical_level)
        )
    
    def _get_mountain_day(self, request: TripRequest) -> Optional[int]:
        """Extract mountain day from constraints."""
        for constraint in request.constraints:
            c_lower = constraint.lower()
            if "mountain" in c_lower or "гор" in c_lower or "озёр" in c_lower:
                for i in range(1, 10):
                    if str(i) in constraint or f"день {i}" in c_lower or f"day {i}" in c_lower:
                        return i
                return request.duration_days
        
        if "nature" in request.interests or "adventure" in request.interests:
            return request.duration_days
        
        return None
    
    def _generate_ai_route(
        self,
        trip_request: TripRequest,
        pois: List[POI],
        mountain_pois: List[POI],
        mountain_day: Optional[int],
        tips: List[str],
        style: str
    ) -> Optional[Route]:
        """Generate a route using LLM."""
        
        try:
            # Prepare POI data for LLM
            poi_data = self._prepare_poi_data(pois, style)
            mountain_data = self._prepare_poi_data(mountain_pois, style) if mountain_pois else []
            
            # Build prompt
            prompt = self._build_generation_prompt(
                trip_request=trip_request,
                poi_data=poi_data,
                mountain_data=mountain_data,
                mountain_day=mountain_day,
                tips=tips,
                style=style
            )
            
            # Generate route using LLM
            response = self.llm_client.complete_json(
                prompt=prompt,
                system_prompt=ROUTE_PLANNER_SYSTEM,
                temperature=0.4
            )
            
            # Parse and validate response
            route = self._parse_llm_response(response, trip_request, style)
            return route
            
        except Exception as e:
            print(f"⚠️ AI generation failed for {style}: {e}")
            # Fallback to algorithmic generation
            return self._generate_fallback_route(
                trip_request, pois, mountain_pois, mountain_day, style
            )
    
    def _prepare_poi_data(self, pois: List[POI], style: str) -> List[Dict]:
        """Prepare POI data for LLM prompt."""
        
        # Filter and sort based on style
        if style == "budget":
            sorted_pois = sorted(pois, key=lambda p: (p.cost_usd, -len([t for t in p.tags if t == "must-see"])))
        elif style == "comfort":
            sorted_pois = sorted(pois, key=lambda p: (-(getattr(p, 'avg_rating', 4.0) or 4.0), -p.cost_usd))
        else:
            sorted_pois = sorted(pois, key=lambda p: (-10 if "must-see" in p.tags else 0, p.cost_usd))
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category[0] if p.category else "attraction",
                "cost": p.cost_usd,
                "hours": p.duration_hours,
                "tags": p.tags[:3],
                "coords": {"lat": p.coordinates.lat, "lng": p.coordinates.lng} if p.coordinates else None
            }
            for p in sorted_pois[:20]
        ]
    
    def _build_generation_prompt(
        self,
        trip_request: TripRequest,
        poi_data: List[Dict],
        mountain_data: List[Dict],
        mountain_day: Optional[int],
        tips: List[str],
        style: str
    ) -> str:
        """Build prompt for LLM route generation."""
        
        style_instructions = {
            "budget": "Выбирай дешёвые и бесплатные места. Максимум $5-7 на активность.",
            "balanced": "Оптимальное сочетание цены и качества. Включи must-see места.",
            "comfort": "Премиальный опыт. Меньше мест, больше времени на каждое. Лучшие рейтинги."
        }
        
        style_names = {
            "budget": "Бюджетный маршрут",
            "balanced": "Сбалансированный маршрут",
            "comfort": "Комфортный маршрут"
        }
        
        prompt = f"""Создай {style_names[style]} для туриста.

ЗАПРОС ТУРИСТА:
- Город: {trip_request.city}
- Дней: {trip_request.duration_days}
- Бюджет: ${trip_request.budget_usd}
- Интересы: {', '.join(trip_request.interests) if trip_request.interests else 'история, культура'}
- Темп: {trip_request.pace.value if hasattr(trip_request.pace, 'value') else trip_request.pace}
- Ограничения: {', '.join(trip_request.constraints) if trip_request.constraints else 'нет'}

СТИЛЬ: {style_instructions[style]}

ДОСТУПНЫЕ МЕСТА (выбери подходящие):
{json.dumps(poi_data, ensure_ascii=False, indent=2)}
"""

        if mountain_day and mountain_data:
            prompt += f"""
ГОРНЫЕ ТУРЫ (для дня {mountain_day}):
{json.dumps(mountain_data, ensure_ascii=False, indent=2)}
"""

        if tips:
            prompt += f"""
СОВЕТЫ:
{chr(10).join('- ' + t for t in tips[:5])}
"""

        prompt += """
ФОРМАТ ОТВЕТА (JSON):
{
    "name": "Название маршрута",
    "description": "Краткое описание (1-2 предложения)",
    "total_cost": числом в USD,
    "days": [
        {
            "day": 1,
            "theme": "Тема дня",
            "activities": [
                {
                    "poi_id": "id места",
                    "poi_name": "Название",
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "cost": числом,
                    "notes": "опционально"
                }
            ]
        }
    ],
    "highlights": ["фишка 1", "фишка 2"],
    "warnings": ["предупреждение если есть"]
}
"""
        return prompt
    
    def _parse_llm_response(
        self,
        response: Dict,
        request: TripRequest,
        style: str
    ) -> Optional[Route]:
        """Parse LLM response into Route object."""
        
        try:
            days = []
            
            for day_data in response.get("days", []):
                activities = []
                day_cost = 0
                day_hours = 0
                
                for act_data in day_data.get("activities", []):
                    cost = float(act_data.get("cost", 0))
                    
                    # Calculate hours from time
                    try:
                        start = datetime.strptime(act_data.get("start_time", "09:00"), "%H:%M")
                        end = datetime.strptime(act_data.get("end_time", "10:00"), "%H:%M")
                        hours = (end - start).seconds / 3600
                    except:
                        hours = 1.5
                    
                    activities.append(ActivitySlot(
                        poi_id=act_data.get("poi_id", "unknown"),
                        poi_name=act_data.get("poi_name", "Место"),
                        start_time=act_data.get("start_time", "09:00"),
                        end_time=act_data.get("end_time", "10:00"),
                        cost_usd=cost,
                        notes=act_data.get("notes")
                    ))
                    
                    day_cost += cost
                    day_hours += hours
                
                if activities:
                    days.append(DayPlan(
                        day=day_data.get("day", len(days) + 1),
                        theme=day_data.get("theme", f"День {len(days) + 1}"),
                        activities=activities,
                        total_cost=day_cost,
                        total_hours=day_hours,
                        notes=day_data.get("notes")
                    ))
            
            if not days:
                return None
            
            style_map = {
                "budget": BudgetStyle.BUDGET,
                "balanced": BudgetStyle.MODERATE,
                "comfort": BudgetStyle.COMFORT
            }
            
            return Route(
                id=f"ai_{style}_{datetime.now().strftime('%H%M%S')}",
                name=response.get("name", f"AI Маршрут ({style})"),
                description=response.get("description", "Сгенерировано AI"),
                duration_days=len(days),
                total_cost_usd=float(response.get("total_cost", sum(d.total_cost for d in days))),
                style=style_map.get(style, BudgetStyle.MODERATE),
                days=days,
                highlights=response.get("highlights", []),
                warnings=response.get("warnings", [])
            )
            
        except Exception as e:
            print(f"⚠️ Error parsing LLM response: {e}")
            return None
    
    def _generate_fallback_route(
        self,
        request: TripRequest,
        pois: List[POI],
        mountain_pois: List[POI],
        mountain_day: Optional[int],
        style: str
    ) -> Optional[Route]:
        """Generate route algorithmically as fallback."""
        
        days = []
        used_pois = set()
        
        # Parameters based on style
        if style == "budget":
            daily_budget = (request.budget_usd / request.duration_days) * 0.5
            prefer_free = True
        elif style == "comfort":
            daily_budget = (request.budget_usd / request.duration_days) * 1.2
            prefer_free = False
        else:
            daily_budget = (request.budget_usd / request.duration_days) * 0.8
            prefer_free = False
        
        hours_per_day = 7
        
        # Sort POIs
        sorted_pois = sorted(
            pois,
            key=lambda p: (
                -10 if "must-see" in p.tags else 0,
                -p.cost_usd if prefer_free else p.cost_usd * 0.1,
                -(getattr(p, 'avg_rating', 4.0) or 4.0)
            )
        )
        
        for day_num in range(1, request.duration_days + 1):
            activities = []
            day_cost = 0.0
            day_hours = 0.0
            current_time = datetime.strptime("09:00", "%H:%M")
            
            # Mountain day
            if day_num == mountain_day and mountain_pois:
                mountain = mountain_pois[0] if style == "budget" else mountain_pois[-1] if len(mountain_pois) > 1 else mountain_pois[0]
                activities.append(ActivitySlot(
                    poi_id=mountain.id,
                    poi_name=mountain.name,
                    start_time="07:00",
                    end_time="17:00",
                    cost_usd=mountain.cost_usd,
                    notes="Полный день в горах"
                ))
                days.append(DayPlan(
                    day=day_num,
                    theme="Горы и природа 🏔️",
                    activities=activities,
                    total_cost=mountain.cost_usd,
                    total_hours=10,
                    notes="Выезд рано утром"
                ))
                continue
            
            # City day
            for poi in sorted_pois:
                if poi.id in used_pois:
                    continue
                if "day_trip" in poi.tags or poi.duration_hours >= 5:
                    continue
                if day_hours + poi.duration_hours > hours_per_day:
                    continue
                if style == "budget" and day_cost + poi.cost_usd > daily_budget:
                    continue
                
                end_time = current_time + timedelta(hours=poi.duration_hours)
                
                activities.append(ActivitySlot(
                    poi_id=poi.id,
                    poi_name=poi.name,
                    start_time=current_time.strftime("%H:%M"),
                    end_time=end_time.strftime("%H:%M"),
                    cost_usd=poi.cost_usd,
                    notes=poi.tips[0] if poi.tips else None
                ))
                
                used_pois.add(poi.id)
                day_cost += poi.cost_usd
                day_hours += poi.duration_hours
                current_time = end_time + timedelta(minutes=30)
                
                if len(activities) >= 6:
                    break
            
            if activities:
                theme = "Исторический центр 🏛️" if day_num == 1 else f"День {day_num}"
                days.append(DayPlan(
                    day=day_num,
                    theme=theme,
                    activities=activities,
                    total_cost=day_cost,
                    total_hours=day_hours
                ))
        
        if not days:
            return None
        
        style_names = {
            "budget": "Бюджетный маршрут",
            "balanced": "Сбалансированный маршрут",
            "comfort": "Комфортный маршрут"
        }
        
        style_map = {
            "budget": BudgetStyle.BUDGET,
            "balanced": BudgetStyle.MODERATE,
            "comfort": BudgetStyle.COMFORT
        }
        
        return Route(
            id=f"fallback_{style}",
            name=style_names.get(style, "Маршрут"),
            description="Сгенерировано алгоритмически",
            duration_days=len(days),
            total_cost_usd=sum(d.total_cost for d in days),
            style=style_map.get(style, BudgetStyle.MODERATE),
            days=days,
            highlights=["Оптимизированный маршрут"],
            warnings=[]
        )


# Backward compatibility alias
RoutePlanner = AIRoutePlanner


# Quick test
if __name__ == "__main__":
    from src.agents.intake import IntakeAgent
    
    intake = IntakeAgent()
    planner = AIRoutePlanner()
    
    test_cases = [
        "2 дня Самарканд, $100, на 2-й день хочу в горы",
        "1 день Самарканд, $50",
        "3 дня, бюджет $200, интересует еда и культура"
    ]
    
    for user_input in test_cases:
        print(f"\n{'='*60}")
        print(f"📝 Input: {user_input}")
        
        request, _ = intake.parse(user_input)
        routes, evidence = planner.generate_routes(request)
        
        print(f"✅ Generated {len(routes)} AI routes")
        print(f"📊 Evidence: {len(evidence.poi_ids)} POIs used")
        
        for route in routes:
            print(f"\n  🗺️ {route.name} — ${route.total_cost_usd:.0f}")
            for day in route.days:
                print(f"     Day {day.day}: {day.theme} ({len(day.activities)} activities)")


# ==================== DETERMINISTIC TRIP PLANNER (Step 4) ====================

class DeterministicTripPlanner:
    """
    No-LLM Trip Planner using pure data-driven scheduling.
    Returns PlanResponse-compatible dicts with days[], blocks[], warnings[].
    """
    
    PACE_CONFIG = {
        "slow": (2, 3),
        "medium": (3, 4),
        "fast": (5, 6)
    }
    
    DAY_THEMES = {
        1: "Сердце Самарканда",
        2: "Древние тайны",
        3: "Культура и вкусы",
        4: "За пределами туризма",
        5: "Неспешный ритм",
    }
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "database"
        self.data_dir = data_dir
        self.poi_data: List[Dict[str, Any]] = []
        self.restaurants: List[Dict[str, Any]] = []
        self.poi_index: Dict[str, Dict[str, Any]] = {}
        self.restaurant_index: Dict[str, Dict[str, Any]] = {}
        self._load_data()
    
    def _load_data(self):
        """Load POI and restaurant data."""
        poi_path = self.data_dir / "poi.json"
        hr_path = self.data_dir / "hotels_restaurants.json"
        
        if poi_path.exists():
            with open(poi_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.poi_data = data.get("poi", [])
                self.poi_index = {p["id"]: p for p in self.poi_data}
        
        if hr_path.exists():
            with open(hr_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.restaurants = data.get("restaurants", [])
                self.restaurant_index = {r["id"]: r for r in self.restaurants}
    
    def create_plan(
        self,
        days: int,
        interests: List[str],
        budget: float,
        pace: str = "medium",
        start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a deterministic trip plan. Returns PlanResponse-compatible dict."""
        warnings: List[str] = []
        plan_days: List[Dict[str, Any]] = []
        total_cost = 0.0
        poi_count = 0
        meal_count = 0
        
        min_poi, max_poi = self.PACE_CONFIG.get(pace, (3, 4))
        scored_pois = self._score_pois(interests)
        used_poi_ids = set()
        
        if start_date:
            try:
                current_date = datetime.strptime(start_date, "%Y-%m-%d")
            except:
                current_date = datetime.now()
        else:
            current_date = datetime.now()
        
        for day_num in range(1, days + 1):
            day_date = current_date + timedelta(days=day_num - 1)
            blocks: List[Dict[str, Any]] = []
            day_cost = 0.0
            
            day_pois = self._select_pois_for_day(scored_pois, used_poi_ids, min_poi, max_poi, day_num)
            for pid in day_pois:
                used_poi_ids.add(pid)
            
            current_time = datetime.strptime("09:00", "%H:%M")
            
            # Morning POIs
            morning_pois = [p for p in day_pois if self.poi_index.get(p, {}).get("best_time") == "morning"]
            other_pois = [p for p in day_pois if p not in morning_pois]
            
            if not morning_pois and other_pois:
                morning_pois = [other_pois.pop(0)]
            
            for poi_id in morning_pois[:2]:
                poi = self.poi_index.get(poi_id, {})
                duration = poi.get("duration_hours", 1.5)
                cost = poi.get("cost_usd", 0)
                
                start_time = current_time.strftime("%H:%M")
                end_time = (current_time + timedelta(hours=duration)).strftime("%H:%M")
                
                blocks.append({
                    "start": start_time, "end": end_time, "type": "poi",
                    "poi_id": poi_id, "venue_id": None,
                    "name": poi.get("name_en") or poi.get("name", poi_id),
                    "reason": self._get_reason(poi), "cost_usd": cost
                })
                day_cost += cost
                poi_count += 1
                current_time = current_time + timedelta(hours=duration, minutes=15)
            
            # Lunch - schedule after morning POIs, but not before 12:00
            lunch_start = max(current_time, datetime.strptime("12:00", "%H:%M"))
            lunch_end = lunch_start + timedelta(hours=1, minutes=30)
            
            lunch_rest = self._select_restaurant(lunch_start.strftime("%H:%M"), budget / days / 3)
            if lunch_rest:
                blocks.append({
                    "start": lunch_start.strftime("%H:%M"), 
                    "end": lunch_end.strftime("%H:%M"), 
                    "type": "meal",
                    "poi_id": None, "venue_id": lunch_rest["id"],
                    "name": f"Обед: {lunch_rest['name']}",
                    "reason": f"{lunch_rest.get('category', 'restaurant').title()} кухня",
                    "cost_usd": lunch_rest.get("avg_check_usd", 15)
                })
                day_cost += lunch_rest.get("avg_check_usd", 15)
                meal_count += 1
            
            current_time = lunch_end + timedelta(minutes=15)

            
            # Afternoon POIs
            for poi_id in other_pois[:2]:
                poi = self.poi_index.get(poi_id, {})
                duration = poi.get("duration_hours", 1.5)
                cost = poi.get("cost_usd", 0)
                
                start_time = current_time.strftime("%H:%M")
                end_time = (current_time + timedelta(hours=duration)).strftime("%H:%M")
                
                blocks.append({
                    "start": start_time, "end": end_time, "type": "poi",
                    "poi_id": poi_id, "venue_id": None,
                    "name": poi.get("name_en") or poi.get("name", poi_id),
                    "reason": self._get_reason(poi), "cost_usd": cost
                })
                day_cost += cost
                poi_count += 1
                current_time = current_time + timedelta(hours=duration, minutes=20)
            
            # Optional dinner
            if budget > day_cost + 20:
                dinner_rest = self._select_restaurant("19:00", budget / days / 3, 
                                                       exclude=lunch_rest["id"] if lunch_rest else None)
                if dinner_rest:
                    blocks.append({
                        "start": "19:30", "end": "21:00", "type": "meal",
                        "poi_id": None, "venue_id": dinner_rest["id"],
                        "name": f"Ужин: {dinner_rest['name']}",
                        "reason": dinner_rest.get("description", "")[:50],
                        "cost_usd": dinner_rest.get("avg_check_usd", 20)
                    })
                    day_cost += dinner_rest.get("avg_check_usd", 20)
                    meal_count += 1
            
            blocks.sort(key=lambda b: b["start"])
            
            plan_days.append({
                "day_number": day_num,
                "date": day_date.strftime("%Y-%m-%d"),
                "theme": f"День {day_num}: {self.DAY_THEMES.get(day_num, 'Исследование')}",
                "blocks": blocks
            })
            total_cost += day_cost
        
        # Quality gates
        if total_cost > budget:
            warnings.append(f"⚠️ Estimated cost ${total_cost:.0f} exceeds budget ${budget:.0f}")
        
        issues = self._validate_plan(plan_days)
        warnings.extend(issues)
        
        return {
            "days": plan_days, "warnings": warnings,
            "total_cost_usd": round(total_cost, 2), "pace": pace,
            "poi_count": poi_count, "meal_count": meal_count
        }
    
    def _score_pois(self, interests: List[str]) -> List[Tuple[str, float]]:
        """Score POIs by relevance to interests."""
        scored = []
        for poi in self.poi_data:
            score = 0.0
            tags = poi.get("tags", [])
            categories = poi.get("category", [])
            
            for interest in interests:
                il = interest.lower()
                if il in tags: score += 2.0
                if il in categories: score += 1.5
                if il in poi.get("description", "").lower(): score += 0.5
            
            if "must-see" in tags: score += 3.0
            if "unesco" in tags: score += 2.0
            score += (poi.get("avg_rating", 4.0) - 4.0) * 0.5
            
            scored.append((poi.get("id"), score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def _select_pois_for_day(self, scored, used, min_c, max_c, day_num) -> List[str]:
        selected = []
        for poi_id, _ in scored:
            if poi_id in used: continue
            if len(selected) >= max_c: break
            poi = self.poi_index.get(poi_id, {})
            if day_num == 1 and "day_trip" in poi.get("category", []): continue
            if "overnight" in poi.get("category", []): continue
            selected.append(poi_id)
        return selected
    
    def _get_reason(self, poi: Dict[str, Any]) -> str:
        best_time = poi.get("best_time", "any")
        tags = poi.get("tags", [])
        if best_time == "morning": return "Лучший утренний свет"
        if best_time == "sunset": return "Невероятный закат"
        if "must-see" in tags: return "Обязательно к посещению"
        if "unesco" in tags: return "Объект ЮНЕСКО"
        return poi.get("description", "")[:40] + "..."
    
    def _select_restaurant(self, time: str, max_price: float, exclude=None) -> Optional[Dict]:
        try:
            time_dt = datetime.strptime(time, "%H:%M")
        except:
            return None
        
        candidates = []
        for rest in self.restaurants:
            if rest["id"] == exclude: continue
            opens = rest.get("opens_at", "00:00")
            closes = rest.get("closing_hours", "23:59")
            try:
                opens_dt = datetime.strptime(opens, "%H:%M")
                closes_dt = datetime.strptime(closes, "%H:%M")
                if closes_dt <= opens_dt: closes_dt = datetime.strptime("23:59", "%H:%M")
                if not (opens_dt <= time_dt <= closes_dt): continue
            except: pass
            
            if rest.get("avg_check_usd", 15) <= max_price * 1.5:
                candidates.append((rest, rest.get("rating", 4.0)))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0] if candidates else None
    
    def _validate_plan(self, plan_days: List[Dict]) -> List[str]:
        """Quality Gates - Step 5."""
        issues = []
        for day in plan_days:
            blocks = day.get("blocks", [])
            for block in blocks:
                if block.get("poi_id") and block["poi_id"] not in self.poi_index:
                    issues.append(f"Unknown POI: {block['poi_id']}")
                if block.get("venue_id") and block["venue_id"] not in self.restaurant_index:
                    issues.append(f"Unknown restaurant: {block['venue_id']}")
            
            for i in range(len(blocks) - 1):
                if blocks[i]["end"] > blocks[i + 1]["start"]:
                    issues.append(f"Time overlap in day {day['day_number']}")
        return issues

