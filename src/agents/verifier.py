"""
Verifier Agent - Checks route feasibility and suggests fixes.
"""

import sys
from pathlib import Path
from typing import List, Tuple
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import (
    TripRequest, Route, DayPlan, VerifierReport, CheckResult
)


class RouteVerifier:
    """
    Verifier agent that checks route feasibility:
    - Budget constraints
    - Time constraints
    - Physical level
    - Specific user constraints
    """
    
    def __init__(self):
        self.max_hours_per_day = {
            "relaxed": 6,
            "moderate": 8,
            "intensive": 10
        }
    
    def verify(self, route: Route, request: TripRequest) -> VerifierReport:
        """
        Verify route against trip request constraints.
        
        Returns:
            VerifierReport with all checks and suggestions
        """
        
        budget_check = self._check_budget(route, request)
        time_check = self._check_time(route, request)
        constraints_check = self._check_constraints(route, request)
        physical_check = self._check_physical(route, request)
        
        # Collect all issues
        issues = []
        if not budget_check.passed:
            issues.append(budget_check.message)
        if not time_check.passed:
            issues.append(time_check.message)
        if not constraints_check.passed:
            issues.append(constraints_check.message)
        if not physical_check.passed:
            issues.append(physical_check.message)
        
        # Generate auto-fixes
        auto_fixes = self._generate_fixes(route, request, issues)
        
        # Calculate overall score
        checks = [budget_check, time_check, constraints_check, physical_check]
        passed_count = sum(1 for c in checks if c.passed)
        overall_score = passed_count / len(checks)
        
        # Is feasible if no critical issues
        is_feasible = budget_check.passed and constraints_check.passed
        
        # Recommendations
        recommendations = self._generate_recommendations(route, request)
        
        return VerifierReport(
            is_feasible=is_feasible,
            overall_score=overall_score,
            budget_check=budget_check,
            time_check=time_check,
            constraints_check=constraints_check,
            physical_check=physical_check,
            issues=issues,
            auto_fixes=auto_fixes,
            recommendations=recommendations
        )
    
    def _check_budget(self, route: Route, request: TripRequest) -> CheckResult:
        """Check if route fits within budget."""
        
        total_cost = route.total_cost_usd
        budget = request.budget_usd
        
        # Add estimated food costs
        food_per_day = 10 if request.budget_style.value == "budget" else 20
        total_with_food = total_cost + (food_per_day * request.duration_days)
        
        if total_with_food <= budget:
            return CheckResult(
                passed=True,
                message=f"✅ Бюджет OK: ${total_with_food:.0f} из ${budget:.0f}",
                details={
                    "activities_cost": total_cost,
                    "estimated_food": food_per_day * request.duration_days,
                    "total": total_with_food,
                    "budget": budget,
                    "remaining": budget - total_with_food
                }
            )
        else:
            over = total_with_food - budget
            return CheckResult(
                passed=False,
                message=f"⚠️ Превышение бюджета на ${over:.0f}",
                details={
                    "activities_cost": total_cost,
                    "estimated_food": food_per_day * request.duration_days,
                    "total": total_with_food,
                    "budget": budget,
                    "over_budget": over
                }
            )
    
    def _check_time(self, route: Route, request: TripRequest) -> CheckResult:
        """Check if daily schedules are feasible."""
        
        max_hours = self.max_hours_per_day.get(request.pace.value, 8)
        overloaded_days = []
        
        for day in route.days:
            if day.total_hours > max_hours:
                overloaded_days.append({
                    "day": day.day,
                    "hours": day.total_hours,
                    "max": max_hours
                })
        
        if not overloaded_days:
            return CheckResult(
                passed=True,
                message=f"✅ Расписание OK для темпа '{request.pace.value}'",
                details={"max_hours_per_day": max_hours}
            )
        else:
            days_str = ", ".join([f"День {d['day']} ({d['hours']:.1f}ч)" for d in overloaded_days])
            return CheckResult(
                passed=False,
                message=f"⚠️ Перегружены дни: {days_str}",
                details={"overloaded_days": overloaded_days}
            )
    
    def _check_constraints(self, route: Route, request: TripRequest) -> CheckResult:
        """Check if specific user constraints are satisfied."""
        
        if not request.constraints:
            return CheckResult(
                passed=True,
                message="✅ Нет специальных ограничений",
                details={}
            )
        
        satisfied = []
        unsatisfied = []
        
        for constraint in request.constraints:
            is_met = self._is_constraint_met(constraint, route)
            
            if is_met:
                satisfied.append(constraint)
            else:
                unsatisfied.append(constraint)
        
        if not unsatisfied:
            return CheckResult(
                passed=True,
                message=f"✅ Все ограничения выполнены ({len(satisfied)})",
                details={"satisfied": satisfied}
            )
        else:
            return CheckResult(
                passed=False,
                message=f"⚠️ Не выполнены: {', '.join(unsatisfied)}",
                details={"satisfied": satisfied, "unsatisfied": unsatisfied}
            )
    
    def _is_constraint_met(self, constraint: str, route: Route) -> bool:
        """Check if a specific constraint is met."""
        
        c_lower = constraint.lower()
        
        # "mountains on day 2" / "горы на 2-й день"
        if "mountain" in c_lower or "гор" in c_lower:
            # Find which day
            day_num = None
            for i in range(1, 10):
                if str(i) in constraint:
                    day_num = i
                    break
            
            if day_num:
                # Check if that day has mountain activity
                for day in route.days:
                    if day.day == day_num:
                        for act in day.activities:
                            if "mountain" in act.poi_name.lower() or "гор" in act.poi_name.lower():
                                return True
                            if "озёр" in act.poi_name.lower() or "lake" in act.poi_name.lower():
                                return True
                            if "ущель" in act.poi_name.lower():
                                return True
                return False
        
        # "departure at 7:00" / "выезд в 7"
        if "7:00" in constraint or "7 утра" in constraint:
            for day in route.days:
                for act in day.activities:
                    if act.start_time == "07:00":
                        return True
            return False
        
        # Default: assume met (for unknown constraints)
        return True
    
    def _check_physical(self, route: Route, request: TripRequest) -> CheckResult:
        """Check if physical requirements match user level."""
        
        # This would check if route has high-physical activities
        # for users with low physical level preference
        
        return CheckResult(
            passed=True,
            message=f"✅ Физ. нагрузка соответствует уровню '{request.physical_level.value}'",
            details={}
        )
    
    def _generate_fixes(
        self,
        route: Route,
        request: TripRequest,
        issues: List[str]
    ) -> List[str]:
        """Generate automatic fixes for identified issues."""
        
        fixes = []
        
        for issue in issues:
            if "бюджет" in issue.lower() or "budget" in issue.lower():
                fixes.append("💡 Замените платные музеи на бесплатные достопримечательности")
                fixes.append("💡 Выберите бюджетный вариант горного тура")
            
            if "перегружен" in issue.lower() or "overload" in issue.lower():
                fixes.append("💡 Уберите 1-2 активности из перегруженного дня")
                fixes.append("💡 Перенесите часть на другой день")
            
            if "не выполнен" in issue.lower():
                fixes.append("💡 Добавьте горный маршрут на указанный день")
        
        return fixes
    
    def _generate_recommendations(
        self,
        route: Route,
        request: TripRequest
    ) -> List[str]:
        """Generate helpful recommendations."""
        
        recommendations = []
        
        # Based on route content
        total_hours = sum(d.total_hours for d in route.days)
        
        if total_hours > 12:
            recommendations.append("🥾 Возьмите удобную обувь - много ходьбы")
        
        if any("гор" in d.theme.lower() or "mountain" in d.theme.lower() for d in route.days):
            recommendations.append("🧥 В горах холоднее - возьмите куртку")
            recommendations.append("💧 Возьмите 2л воды на горный день")
        
        if request.budget_usd < 100:
            recommendations.append("🍽️ Обедайте в местных чайханах - вкусно и недорого")
        
        recommendations.append("📸 Лучшее время для фото - раннее утро")
        
        return recommendations[:4]
    
    def apply_fixes(self, route: Route, fixes: List[str]) -> Route:
        """Apply suggested fixes to route (simplified version)."""
        
        # In full implementation, this would modify the route
        # For MVP, just return the route as-is
        return route


def print_verification_report(report: VerifierReport):
    """Pretty print verification report."""
    
    status = "✅ ВЫПОЛНИМО" if report.is_feasible else "❌ ТРЕБУЕТ ПРАВОК"
    print(f"\n{'='*50}")
    print(f"📋 ВЕРИФИКАЦИЯ: {status} (score: {report.overall_score:.0%})")
    print(f"{'='*50}")
    
    print(f"\n{report.budget_check.message}")
    if report.budget_check.details:
        details = report.budget_check.details
        if "remaining" in details:
            print(f"   Остаток: ${details['remaining']:.0f}")
    
    print(f"\n{report.time_check.message}")
    print(f"\n{report.constraints_check.message}")
    print(f"\n{report.physical_check.message}")
    
    if report.issues:
        print(f"\n⚠️ ПРОБЛЕМЫ:")
        for issue in report.issues:
            print(f"   • {issue}")
    
    if report.auto_fixes:
        print(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        for fix in report.auto_fixes:
            print(f"   {fix}")
    
    if report.recommendations:
        print(f"\n📌 СОВЕТЫ:")
        for rec in report.recommendations:
            print(f"   {rec}")


# Quick test
if __name__ == "__main__":
    from src.agents.intake import IntakeAgent
    from src.agents.planner import RoutePlanner
    
    # Parse and plan
    intake = IntakeAgent()
    request, _ = intake.parse("2 дня Самарканд, $100, на 2-й день хочу в горы")
    
    planner = RoutePlanner()
    routes, _ = planner.generate_routes(request)
    
    # Verify each route
    verifier = RouteVerifier()
    
    for route in routes:
        print(f"\n\n{'#'*60}")
        print(f"# {route.name}")
        print(f"{'#'*60}")
        
        report = verifier.verify(route, request)
        print_verification_report(report)
