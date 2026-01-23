"""
Intake Agent - Parses user input into structured TripRequest.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Optional, Tuple, List, Any
from src.models.schemas import TripRequest, TripPace
from src.utils.llm import get_llm_client


SYSTEM_PROMPT = """You are a travel planning assistant for Uzbekistan tourism.
Your job is to extract structured trip requirements from user messages.

Rules:
1. Extract all mentioned constraints (dates, budget, interests, specific requirements)
2. If critical information is missing, ask ONE clarifying question
3. Convert informal language to structured data
4. Default city is Samarkand unless otherwise specified
5. Respond in the same language as the user

For constraints like "горы на 2-й день" or "mountains on day 2", add to constraints list.
"""

EXTRACTION_PROMPT_TEMPLATE = """
Parse this trip request into structured data:

User message: "{user_input}"

Extract:
- duration_days (required)
- budget_usd (required, convert from local currency if needed)
- interests (list of interests: history, nature, food, architecture, culture, adventure, etc.)
- constraints (specific requirements like "mountains on day 2", "departure at 7:00")
- pace (relaxed/moderate/intensive)
- travelers_count (default 1)

If any REQUIRED field is missing or unclear, respond with:
{{"needs_clarification": true, "question": "your single clarifying question"}}

If all required fields are clear, respond with the TripRequest JSON:
{{"needs_clarification": false, "trip_request": {{...all fields...}}}}

Respond ONLY with valid JSON.
"""


class IntakeAgent:
    """
    Agent that converts natural language trip requests 
    into structured TripRequest objects.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client or get_llm_client()
        self.conversation_history: List[dict] = []
    
    def parse(self, user_input: str) -> Tuple[Optional[TripRequest], Optional[str]]:
        """
        Parse user input into TripRequest.
        
        Returns:
            (TripRequest, None) if parsing successful
            (None, question) if clarification needed
        """
        
        # Check for greetings - ask for trip details first
        greetings = ['hello', 'hi', 'hey', 'salom', 'привет', 'здравствуйте', 'assalomu', 'privet']
        if user_input.lower().strip() in greetings or len(user_input.strip()) < 5:
            return None, "How many days would you like to travel and what's your budget? What interests you - history, food, nature?"
        
        # For simple inputs with trip keywords, use mock parser directly (more reliable)
        simple_patterns = ['day', 'дн', 'kun', '$', 'budget', 'бюджет', 'trip', 'travel']
        if len(user_input.split()) <= 8 or any(p in user_input.lower() for p in simple_patterns):
            return self._mock_parse(user_input)
        
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(user_input=user_input)
        
        try:
            result = self.llm.complete_json(prompt, SYSTEM_PROMPT)
        except Exception as e:
            # Fallback to mock parsing for demo
            return self._mock_parse(user_input)
        
        if result.get("needs_clarification"):
            # Don't ask for clarification, just use defaults
            return self._mock_parse(user_input)
        
        trip_data = result.get("trip_request", {})
        
        # Normalize and validate
        trip_data["city"] = trip_data.get("city", "Samarkand")
        trip_data["pace"] = trip_data.get("pace", "moderate")
        
        # Default budget if not specified or 0
        if not trip_data.get("budget_usd") or trip_data.get("budget_usd", 0) < 10:
            trip_data["budget_usd"] = 100  # Default $100 for budget trips
        
        # Default duration if not specified
        if not trip_data.get("duration_days") or trip_data.get("duration_days", 0) < 1:
            trip_data["duration_days"] = 2  # Default 2 days
        
        # Default pace if not specified or invalid
        valid_paces = ['relaxed', 'moderate', 'intensive']
        if not trip_data.get("pace") or trip_data.get("pace") not in valid_paces:
            trip_data["pace"] = "moderate"
        
        # Default interests if empty
        if not trip_data.get("interests"):
            trip_data["interests"] = ["history", "architecture"]
        
        try:
            trip_request = TripRequest.model_validate(trip_data)
            return trip_request, None
        except Exception as e:
            return None, f"Could not parse request: {e}"
    
    def _mock_parse(self, user_input: str) -> Tuple[Optional[TripRequest], Optional[str]]:
        """
        Mock parsing for demo without LLM API.
        Extracts basic info using simple heuristics.
        """
        print(f"DEBUG: ENTERING MOCK PARSE with '{user_input}'")
        text = user_input.lower()
        
        # Text-to-number mapping for Russian (1-14)
        text_numbers = {
            'один': 1, 'одну': 1, 'одного': 1,
            'два': 2, 'две': 2, 'двух': 2,
            'три': 3, 'трёх': 3, 'трех': 3,
            'четыре': 4, 'четырёх': 4, 'четырех': 4,
            'пять': 5, 'пяти': 5,
            'шесть': 6, 'шести': 6,
            'семь': 7, 'семи': 7,
            'восемь': 8, 'восьми': 8,
            'девять': 9, 'девяти': 9,
            'десять': 10, 'десяти': 10,
            'одиннадцать': 11, 'одиннадцати': 11,
            'двенадцать': 12, 'двенадцати': 12,
            'тринадцать': 13, 'тринадцати': 13,
            'четырнадцать': 14, 'четырнадцати': 14,
        }
        
        # Extract duration using regex (supports any number)
        import re
        duration = 2  # default
        
        # Check for week-based input first (неделю, две недели, etc.)
        if 'недел' in text:
            print("DEBUG: Checking week based")
            week_count = 1
            for word, num in text_numbers.items():
                if word in text and 'недел' in text:
                    week_count = num
                    break
            duration = week_count * 7
        # Then try digit-based match (3 дня, 10 days)
        elif re.search(r'(\d+)\s*(?:day|days|дня|дней|день|kun|dnya|den)', text):
            print("DEBUG: Checking digit based duration")
            day_match = re.search(r'(\d+)\s*(?:day|days|дня|дней|день|kun|dnya|den)', text)
            duration = int(day_match.group(1))
        else:
            # Try text-based numbers (три дня, пять дней, etc.)
            for word, num in text_numbers.items():
                if re.search(rf'\b{word}\s*(?:дня|дней|день|day|days|kun|dnya|den)', text):
                    duration = num
                    break
        
        # Validate duration
        if duration > 14:
            duration = 14  # cap at 2 weeks
        elif duration < 1:
            duration = 1
        
        # Extract budget (supports $300, 300$, 300 долларов)
        # Also handles corrections: "ne sto dollarov a 300" (not 100 but 300)
        budget = 100.0  # default
        
        # Check for corrections first (ne sto/not X but Y)
        correction_patterns = [
            r'(?:ne|не|нет)\s*(?:sto|сто|100)\s*(?:dollarov|долларов|usd)?\s*(?:a|а|but|но)\s*(\d+)',
            r'(?:not|не)\s*(\d+)\s*(?:but|а|но)\s*(\d+)',
            r'(\d+)\s*(?:dollarov|долларов|usd|dollar)\s*(?:a|а|but|но)\s*(\d+)',
        ]
        for i, pattern in enumerate(correction_patterns):
            correction_match = re.search(pattern, text, re.IGNORECASE)
            if correction_match:
                # Take the last number (the corrected value)
                budget = float(correction_match.group(2) if correction_match.lastindex >= 2 else correction_match.group(1))
                print(f"DEBUG: Correction match {i}: {budget}")
                break
        
        # If no correction found, try standard patterns
        if budget == 100.0:
            # 1. Check strict suffix first (100$)
            budget_match = re.search(r'(\d+)\s*\$', user_input)
            if budget_match:
                budget = float(budget_match.group(1))
            
            # 2. Check strict prefix ($100) - ensure not part of previous text
            if not budget_match:
                budget_match = re.search(r'(?<!\d)\$\s*(\d+)', user_input)
                if budget_match:
                    budget = float(budget_match.group(1))
            
            # 3. Check text patterns
            if not budget_match:
                budget_match = re.search(r'(\d+)\s*(?:доллар|usd|dollar)', text)
                if budget_match:
                    budget = float(budget_match.group(1))
        
        # Also check for standalone numbers
        if budget == 100.0:
            standalone_numbers = re.findall(r'\b(\d{2,4})\b', user_input)
            for num_str in standalone_numbers:
                num = int(num_str)
                if 50 <= num <= 10000:
                    budget = float(num)
                    break
        
        # Extract interests
        interests = []
        interest_keywords = {
            "history": ["истор", "history", "древн"],
            "nature": ["природ", "nature", "гор", "mountain", "озер", "lake"],
            "food": ["еда", "food", "плов", "plov", "кухн"],
            "architecture": ["архитектур", "architecture", "здан"],
            "culture": ["культур", "culture", "традиц"],
        }
        for interest, keywords in interest_keywords.items():
            if any(kw in text for kw in keywords):
                interests.append(interest)
        
        if not interests:
            interests = ["history", "architecture"]  # default for Samarkand
        
        # Extract constraints
        constraints = []
        if "гор" in text and ("2" in text or "втор" in text):
            constraints.append("mountains on day 2")
        if "7:00" in text or "7 утра" in text:
            constraints.append("departure at 7:00")
        
        
        trip_request = TripRequest(
            city="Samarkand",
            duration_days=duration,
            budget_usd=budget,
            interests=interests,
            constraints=constraints,
            pace=TripPace.MODERATE
        )
        
        return trip_request, None
    
    def apply_patch(self, original: TripRequest, patch_text: str) -> TripRequest:
        """
        Apply a modification to existing TripRequest.
        E.g., "Сделай бюджет $80" -> updates budget_usd to 80
        """
        
        prompt = f"""
Current trip request:
{original.model_dump_json(indent=2)}

User wants to modify: "{patch_text}"

Return the UPDATED trip request as JSON with only the changed fields.
"""
        
        try:
            changes = self.llm.complete_json(prompt)
            
            # Apply changes to original
            current_data = original.model_dump()
            current_data.update(changes)
            
            return TripRequest.model_validate(current_data)
        except:
            # Mock patch for demo
            return self._mock_apply_patch(original, patch_text)
    
    def _mock_apply_patch(self, original: TripRequest, patch_text: str) -> TripRequest:
        """Mock patch application for demo."""
        
        import re
        data = original.model_dump()
        
        # Budget change
        budget_match = re.search(r'\$(\d+)', patch_text)
        if budget_match:
            data["budget_usd"] = float(budget_match.group(1))
        
        # Date/time changes
        if "завтра" in patch_text.lower() or "tomorrow" in patch_text.lower():
            from datetime import date, timedelta
            data["start_date"] = (date.today() + timedelta(days=1)).isoformat()
        
        return TripRequest.model_validate(data)


# Quick test
if __name__ == "__main__":
    agent = IntakeAgent()
    
    test_inputs = [
        "2 дня Самарканд, $100, на 2-й день хочу в горы",
        "Samarkand for 3 days, budget $150, interested in history and food",
        "Хочу посмотреть Регистан и попробовать плов, бюджет $50"
    ]
    
    for user_input in test_inputs:
        print(f"\n📝 Input: {user_input}")
        result, question = agent.parse(user_input)
        
        if question:
            print(f"❓ Need clarification: {question}")
        else:
            print(f"✅ Parsed: {result.model_dump_json(indent=2)}")
