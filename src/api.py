"""
SaFar - AI Travel Assistant API
100% AI-Generated Itineraries using Ollama phi3
"""

import os
import hashlib
from typing import List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

# Import local modules
from src.utils.llm import get_llm_client
from src.agents.intake import IntakeAgent
from src.models.schemas import TripRequest
from src.agents.context_chat import ContextChatAgent
from src.agents.storyteller import CultureStoryteller
from src.utils.weather import WeatherService
from src.rag.retriever import HybridPOIRetriever

app = FastAPI(
    title="SaFar API",
    description="AI-Powered Travel Assistant for Samarkand",
    version="2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (images)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/images", StaticFiles(directory=str(frontend_dir / "images"), html=False), name="images")

# --- Singletons ---
_llm_client = None
_intake_agent = None
_context_chat = None
_storyteller = None
_weather_service = None
_poi_retriever = None
_conversation_history: dict = {}  # session_id -> list of messages

def get_poi_retriever():
    global _poi_retriever
    if _poi_retriever is None:
        _poi_retriever = HybridPOIRetriever()
    return _poi_retriever

def get_llm():
    global _llm_client
    if _llm_client is None:
        _llm_client = get_llm_client()
    return _llm_client

def get_intake_agent():
    global _intake_agent
    if _intake_agent is None:
        _intake_agent = IntakeAgent(get_llm())
    return _intake_agent

def get_context_chat():
    global _context_chat
    if _context_chat is None:
        _context_chat = ContextChatAgent(get_llm())
    return _context_chat

def get_storyteller():
    global _storyteller
    if _storyteller is None:
        _storyteller = CultureStoryteller(get_llm())
    return _storyteller

def get_weather():
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service

def get_poi_image_url(poi_id: str, category: str = "poi") -> str:
    """Map POI ID to image URL. Returns API-served path."""
    # #region agent log
    import json
    log_data = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "A",
        "location": "api.py:get_poi_image_url",
        "message": "POI image URL lookup",
        "data": {"poi_id": poi_id, "category": category},
        "timestamp": int(__import__("time").time() * 1000)
    }
    try:
        with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    # Special mappings for POI IDs that don't match image filenames exactly
    poi_id_mappings = {
        "gur_emir_mausoleum": "gur_e_amir_mausoleum",
        "shah_i_zinda": "shah_i_zinda_necropolis",
        "bibi_khanym_mosque": "bibi_khanym_mosque",
        "siab_bazaar": "siob_bazaar",
        "afrosiyab_museum": "afrosiyob_museum",
        "ulugh_beg_observatory": "ulugh_beg_observatory_museum",
        "hazrat_khizr_mosque": "hazrat_khizr_mosque",
        "central_plov_center": "central_plov_center",  # May not exist, will fallback
        "silk_paper_workshop_konigil": "meros_paper_mill",
        "khovrenko_winery": "khovrenko_winery_wine_museum",
        "rukhobod_mausoleum": "rukhobod_mausoleum",
        "amir_temur_statue": "amir_temur_monument",
        "zarafshan_gorge_day_trip": "amankutan_gorge_viewpoint",  # Fallback
        "seven_lakes_fann_mountains": "amankutan_gorge_viewpoint",  # Fallback
        "aksay_waterfall_hike": "amankutan_gorge_viewpoint",  # Fallback
        "urgut_sunday_market": "urgut_bazaar",
        "siyob_restaurant": "siob_bazaar",  # Fallback
        "art_cafe_samarkand": "siob_bazaar",  # Fallback
        "ishrat_khona_ruins": "ishratkhana_mausoleum",
        "sunset_viewpoint_hill": "hazrat_khizr_viewpoint",
        "samarkand_carpet_workshop": "samarkand_bukhara_silk_carpets_factory",
        "saint_daniel_tomb": "khoja_doniyor_mausoleum",
        "museum_ulughbek": "ulugh_beg_observatory_museum",
        "registan_night_show": "registan_square",
        "teahouse_lyabi_hovuz": "siob_bazaar",  # Fallback
        "afrosiyab_ancient_settlement": "afrosiyob_archaeological_site",
        "eternal_city_samarkand": "registan_square",  # Fallback
        "nurata_mountains_2day": "amankutan_gorge_viewpoint",  # Fallback
        "chorsu_local_market": "siob_bazaar",  # Fallback
    }
    
    # Use mapping if exists, otherwise use POI ID as-is
    image_filename = poi_id_mappings.get(poi_id, poi_id)
    
    # Check if image exists
    frontend_dir = Path(__file__).parent.parent / "frontend"
    image_path = frontend_dir / "images" / category / f"{image_filename}.jpg"
    
    # #region agent log
    log_data2 = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "B",
        "location": "api.py:get_poi_image_url",
        "message": "Image path check",
        "data": {"image_path": str(image_path), "exists": image_path.exists()},
        "timestamp": int(__import__("time").time() * 1000)
    }
    try:
        with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data2) + "\n")
    except:
        pass
    # #endregion
    
    if image_path.exists():
        result = f"/images/{category}/{image_filename}.jpg"
        # #region agent log
        log_data3 = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "C",
            "location": "api.py:get_poi_image_url",
            "message": "Image found",
            "data": {"result": result},
            "timestamp": int(__import__("time").time() * 1000)
        }
        try:
            with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data3) + "\n")
        except:
            pass
        # #endregion
        return result
    
    # Try alternative extensions
    for ext in [".png", ".webp"]:
        alt_path = frontend_dir / "images" / category / f"{image_filename}{ext}"
        if alt_path.exists():
            return f"/images/{category}/{image_filename}{ext}"
    
    # Fallbacks by category (so cards always have a local image)
    fallback_by_category = {
        "hotels": ("hotels", "hotel_city_samarkand.jpg"),
        "restaurants": ("restaurants", "rest_afandi_food.jpg"),
        "poi": ("poi", "registan_square.jpg"),
    }
    fb = fallback_by_category.get(category)
    if fb:
        fb_dir, fb_file = fb
        fb_path = frontend_dir / "images" / fb_dir / fb_file
        if fb_path.exists():
            result = f"/images/{fb_dir}/{fb_file}"
            # #region agent log
            log_data4 = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "location": "api.py:get_poi_image_url",
                "message": "Image not found, using fallback",
                "data": {"poi_id": poi_id, "image_filename": image_filename, "category": category, "fallback": result},
                "timestamp": int(__import__("time").time() * 1000)
            }
            try:
                with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data4) + "\n")
            except:
                pass
            # #endregion
            return result

    # Return empty string if no image found (frontend will use remote fallback)
    # #region agent log
    log_data5 = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "D2",
        "location": "api.py:get_poi_image_url",
        "message": "Image not found, returning empty",
        "data": {"poi_id": poi_id, "image_filename": image_filename, "category": category},
        "timestamp": int(__import__("time").time() * 1000)
    }
    try:
        with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data5) + "\n")
    except:
        pass
    # #endregion
    return ""

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    needs_clarification: bool
    trip_request: Optional[TripRequest] = None

class StoryRequest(BaseModel):
    poi_id: str
    language: str = "ru"
    style: str = "full"

class WeatherRequest(BaseModel):
    days: int = 3

class OptimizeRequest(BaseModel):
    places: List[str]
    days: int = 1
    budget: float = 100

class EditPlanRequest(BaseModel):
    places: List[str]
    instruction: str

# --- AI Itinerary Generation ---
ITINERARY_SYSTEM = """Ты SaFar — лучший AI-гид по Самарканду и Узбекистану.

Твои знания:
- Все достопримечательности Самарканда: Регистан, Гур-Эмир, Шахи-Зинда, Биби-Ханым, Сиаб базар
- Лучшие рестораны: Плов Базар, Карим Плов, Биби-Ханым чойхона
- Отели всех категорий: от хостелов до 5*
- Секретные места, о которых знают только местные
- Практические советы: валюта, транспорт, безопасность

Стиль ответа:
- Используй эмодзи для визуального разделения
- Давай конкретные цены в USD
- Указывай время работы и адреса
- Отвечай на языке пользователя (RU/EN/UZ)
- Будь дружелюбным и полезным"""

ITINERARY_PROMPT = """Создай детальный маршрут на {days} дней по Самарканду.

ПАРАМЕТРЫ:
- Бюджет: ${budget} (включая еду и входные билеты, без жилья)
- Интересы: {interests}
- Стиль: насыщенный, но без спешки

ДЛЯ КАЖДОГО ДНЯ укажи:
1. Тему дня
2. 4-5 активностей с точным временем (09:00 - 10:30)
3. Рекомендации по еде (завтрак, обед, ужин)
4. Стоимость каждой активности
5. Практические советы

ВКЛЮЧИ обязательно:
- Регистан (утром или вечером для лучшего света)
- Гур-Эмир (мавзолей Тамерлана)
- Шахи-Зинда (аллея мавзолеев)
- Сиаб Базар (местный рынок)
- Минимум 1 скрытую жемчужину

В КОНЦЕ дай:
- 💰 Разбивку бюджета
- ⚠️ Важные советы
- 📸 Лучшие фото-споты"""

def generate_ai_itinerary(days: int, budget: float, interests: List[str]) -> str:
    """Use LLM to generate a fully AI-powered itinerary with RAG context."""
    llm = get_llm()
    retriever = get_poi_retriever()
    
    # Get relevant POIs from vector database based on interests
    query = " ".join(interests) + " Samarkand достопримечательности"
    rag_results = retriever.search(query=query, top_k=15)
    
    # Format POI context for the LLM
    poi_context = ""
    if rag_results:
        poi_list = []
        for r in rag_results[:12]:
            poi = r.poi
            poi_info = f"- {poi.name}: {poi.description[:100]}... (${poi.cost_usd}, {poi.duration_hours}ч)"
            poi_list.append(poi_info)
        poi_context = "\n".join(poi_list)
    
    prompt = f"""✨ **ЗАДАЧА: Создать Шедевральный Маршрут** ✨
       
       Дни: {days} | Бюджет: ${budget} | Интересы: {interests}
       
       📍 **ДОСТУПНЫЕ МЕСТА ИЗ БАЗЫ ДАННЫХ:**
       {poi_context if poi_context else "Используй свои знания о Самарканде"}
       
       Ты — элитный AI-гид. Используй ТОЛЬКО места из списка выше для создания маршрута.
       
       ⚡ **ТРЕБОВАНИЯ:**
       - Используй **жирные заголовки** и эмодзи
       - Добавь "✨ Магию момента" к каждому месту
       - Учитывай логистику и время суток
       - Указывай реальные цены из базы данных
       
       🗺️ **ФОРМАТ ОТВЕТА:**
       
       ### 🌟 [Креативное Название Дня]
       > *Вдохновляющая цитата...*
       
       **09:00 — 🏛️ [Название места]**
       ...детали с ценой и временем...
       
       **13:00 — 🍛 Обед**
       ...рекомендации...
       
       💡 **Секрет инсайдера:** ...
       
       В конце: 💰 Итоговый бюджет и 📸 Топ фото-споты.
       """
    
    system = """Ты — SaFar, AI-гид по Самарканду. Используй данные из базы для создания точных маршрутов.
    ВАЖНО: Отвечай на языке пользователя (русский по умолчанию)."""
    
    try:
        response = llm.complete(prompt, system_prompt=system, max_tokens=4000)
        
        # Format the response nicely
        header = f"🗓️ **Ваш {days}-дневный маршрут по Самарканду**\n"
        header += f"💰 Бюджет: ${budget:.0f} | 📍 Самарканд, Узбекистан\n"
        header += f"🔍 Найдено {len(rag_results)} мест в базе данных\n\n"
        
        return header + response
    except Exception as e:
        # Fallback if LLM fails
        return f"❌ Ошибка генерации: {str(e)}. Попробуйте ещё раз."

# --- API Endpoints ---

@app.get("/")
async def root():
    llm = get_llm()
    return {
        "status": "SaFar API is running",
        "llm": type(llm).__name__,
        "version": "2.0 - 100% AI Generated"
    }

@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - parses user request and generates AI itinerary.
    Now with smart clarifying questions and conversation history!
    """
    agent = get_intake_agent()
    session_id = request.session_id or "default"
    
    # Initialize conversation history for this session
    if session_id not in _conversation_history:
        _conversation_history[session_id] = []
    
    # Add user message to history
    _conversation_history[session_id].append({"role": "user", "content": request.message})
    
    # Check for greetings
    greetings = ['hello', 'hi', 'hey', 'salom', 'привет', 'здравствуйте']
    if request.message.lower().strip() in greetings or len(request.message.strip()) < 5:
        _conversation_history[session_id].append({"role": "assistant", "content": "greeting"})
        return ChatResponse(
            message="Привет! Я SaFar — ваш AI-помощник для путешествий по Самарканду. 🏛️\n\nРасскажите о вашей поездке:\n• Сколько дней планируете?\n• Какой бюджет?\n• Что вас интересует? (история, еда, природа, шопинг...)",
            needs_clarification=True,
            trip_request=None
        )
    
    # Check if this is a correction to previous trip request
    # Look for patterns like "ne sto dollarov a 300", "not 100 but 300", etc.
    previous_trip = None
    if len(_conversation_history[session_id]) > 2:
        # Check last assistant response for trip_request
        for msg in reversed(_conversation_history[session_id][:-1]):
            if isinstance(msg, dict) and msg.get("trip_request"):
                previous_trip = msg.get("trip_request")
                break
    
    # If we have a previous trip and this looks like a correction, use apply_patch
    if previous_trip and any(word in request.message.lower() for word in ['ne', 'не', 'not', 'но', 'but', 'а']):
        try:
            from src.models.schemas import TripRequest
            prev_trip_obj = TripRequest.model_validate(previous_trip) if isinstance(previous_trip, dict) else previous_trip
            updated_trip = agent.apply_patch(prev_trip_obj, request.message)
            trip_request = updated_trip
            question = None
        except:
            # Fallback to normal parsing
            trip_request, question = agent.parse(request.message)
    else:
        # Parse user input (will handle corrections in _mock_parse)
        trip_request, question = agent.parse(request.message)
    
    if trip_request:
        # Check if we need clarifying questions
        missing_info = []
        
        # Check for arrival/departure info
        text_lower = request.message.lower()
        has_arrival_info = any(word in text_lower for word in ['прилет', 'arrival', 'прибы', 'приезж', 'утром', 'вечером', 'в ', 'приеду'])
        has_interests = len(trip_request.interests) > 0 and trip_request.interests != ['history', 'architecture']
        
        if not has_arrival_info:
            missing_info.append("🕐 Во сколько вы прибываете в Самарканд?")
        if not has_interests or 'history' in trip_request.interests and 'architecture' in trip_request.interests:
            missing_info.append("🎯 Что вас больше интересует: история, гастрономия, природа, шопинг?")
        
        # Ask clarifying questions if needed (but still remember the trip_request)
        if missing_info and len(missing_info) >= 2:
            clarification_msg = f"Отлично! {trip_request.duration_days} дней с бюджетом ${trip_request.budget_usd:.0f} — хороший план!\n\nЧтобы составить идеальный маршрут, уточните:\n" + "\n".join(missing_info)
            # Store trip_request in history
            _conversation_history[session_id].append({
                "role": "assistant", 
                "content": clarification_msg,
                "trip_request": trip_request.model_dump() if hasattr(trip_request, 'model_dump') else trip_request
            })
            return ChatResponse(
                message=clarification_msg,
                needs_clarification=True,
                trip_request=trip_request  # Keep the parsed request for context
            )
        
        # Generate 100% AI itinerary!
        itinerary = generate_ai_itinerary(
            days=trip_request.duration_days,
            budget=trip_request.budget_usd,
            interests=trip_request.interests
        )
        
        # Store successful trip_request in history
        _conversation_history[session_id].append({
            "role": "assistant",
            "content": itinerary,
            "trip_request": trip_request.model_dump() if hasattr(trip_request, 'model_dump') else trip_request
        })
        return ChatResponse(
            message=itinerary,
            needs_clarification=False,
            trip_request=trip_request
        )
    else:
        return ChatResponse(
            message=question or "Расскажите подробнее: сколько дней, какой бюджет, что хотите увидеть?",
            needs_clarification=True,
            trip_request=None
        )

@app.post("/v1/regenerate")
async def regenerate_itinerary(request: ChatRequest):
    """Regenerate itinerary with different suggestions."""
    agent = get_intake_agent()
    trip_request, _ = agent.parse(request.message)
    
    if trip_request:
        itinerary = generate_ai_itinerary(
            days=trip_request.duration_days,
            budget=trip_request.budget_usd,
            interests=trip_request.interests
        )
        return {"message": itinerary, "regenerated": True}
    
    return {"message": "Could not parse your request", "regenerated": False}

@app.post("/v1/optimize-itinerary")
async def optimize_itinerary(request: OptimizeRequest):
    """Optimize user's selected places into a smart itinerary."""
    llm = get_llm()
    
    places_str = ", ".join(request.places)
    
    prompt = f"""✨ **ЗАДАЧА: Создать Шедевральный Маршрут** ✨
       
       Места: {places_str}
       Дней: {request.days}
       
       Ты — элитный консьерж-сервис уровня Luxury. Твоя задача — не просто составить список, а влюбить гостя в Самарканд.
       
       ⚡ **ТРЕБОВАНИЯ К ОФОРМЛЕНИЮ:**
       - Используй **жирные заголовки** и красивые разделители.
       - Добавь "✨ Магию момента" к каждому месту (почему именно сейчас?).
       - Логистика должна быть идеальной (учитывай время суток).
       - Стиль: Вдохновляющий, легкий, с эмодзи.
       
       🗺️ **СТРУКТУРА ОТВЕТА:**
       
       ### 🌟 [Креативное Название Дня]
       > *Цитата или краткое вдохновение...*
       
       **09:00 — 🏛️ Начало Пути**
       ...детали...
       
       **13:00 — 🍛 Гастрономическая Пауза**
       ...совет по блюдам...
       
       💡 **Секрет инсайдера:** ...
       
       Сделай это красиво!"""
    
    system = "Welcome to SaFar!"
    
    try:
        response = llm.complete(prompt, system_prompt=system, max_tokens=2000)
        
        return {
            "success": True,
            "itinerary": f"✨ **Оптимизированный маршрут**\n\n{response}",
            "places_count": len(request.places),
            "days": request.days
        }
    except Exception as e:
        return {
            "success": False,
            "itinerary": f"❌ Ошибка оптимизации: {str(e)}",
            "places_count": len(request.places),
            "days": request.days
        }

@app.post("/v1/edit-itinerary")
async def edit_itinerary(request: EditPlanRequest):
    """Edit the itinerary plan based on user instruction."""
    llm = get_llm()
    
    prompt = f"""
    Current list of places to visit in Samarkand:
    {', '.join(request.places)}
    
    User Instruction: "{request.instruction}"
    
    Task: Modify the list of places based strictly on the user's instruction.
    - If they say "remove museums", remove them.
    - If they say "add restaurants", add 2-3 popular ones.
    - If they say "make it shorter", remove less important places.
    
    Return a valid JSON object with the NEW list:
    {{
        "places": ["Place 1", "Place 2", ...],
        "message": "Brief explanation of changes"
    }}
    """
    
    try:
        response = llm.complete_json(prompt)
        return response
    except Exception as e:
        # Fallback if JSON fails
        return {"places": request.places, "message": "Failed to edit plan, keeping original."}

@app.get("/v1/places")
async def get_places(category: str = "all", limit: int = 20):
    """Get places from the database."""
    # Return sample places for the frontend
    places = [
        {"id": "1", "name": "Registan Square", "description": "UNESCO World Heritage Site with 3 madrasas", "category": "attraction", "price": 5, "rating": 4.9},
        {"id": "2", "name": "Gur-e-Amir", "description": "Mausoleum of Tamerlane", "category": "attraction", "price": 3, "rating": 4.8},
        {"id": "3", "name": "Shah-i-Zinda", "description": "Avenue of Mausoleums", "category": "attraction", "price": 3, "rating": 4.9},
        {"id": "4", "name": "Bibi-Khanym Mosque", "description": "Historic 15th century mosque", "category": "attraction", "price": 3, "rating": 4.7},
        {"id": "5", "name": "Siab Bazaar", "description": "Traditional market with spices and fruits", "category": "market", "price": 0, "rating": 4.6},
        {"id": "6", "name": "Ulugh Beg Observatory", "description": "15th century astronomical observatory", "category": "attraction", "price": 5, "rating": 4.7},
        {"id": "7", "name": "Boss Plov", "description": "Best plov in Samarkand", "category": "restaurant", "price": 5, "rating": 4.8},
        {"id": "8", "name": "Samarkand Darvoza", "description": "Fine dining with Registan view", "category": "restaurant", "price": 25, "rating": 4.7},
        {"id": "9", "name": "Silk Road Hotel", "description": "5-star luxury hotel", "category": "hotel", "price": 150, "rating": 4.9},
        {"id": "10", "name": "Afrasiab Museum", "description": "Ancient Sogdian artifacts", "category": "attraction", "price": 3, "rating": 4.5},
    ]
    
    if category != "all":
        places = [p for p in places if p["category"] == category]
    
    return {"places": places[:limit]}

@app.get("/v1/search")
async def search_places(q: str = "", category: str = "all", limit: int = 20):
    """Search places - this endpoint is called by the frontend."""
    import json
    from pathlib import Path
    
    places = []
    data_dir = Path(__file__).parent.parent / "data"
    
    # Load POI data
    poi_path = data_dir / "poi.json"
    if poi_path.exists():
        with open(poi_path, "r", encoding="utf-8") as f:
            poi_data = json.load(f)
        for poi in poi_data.get("poi", []):
            poi_id = poi.get("id")
            poi_categories = poi.get("category", [])
            if isinstance(poi_categories, list):
                # Map POI categories to frontend categories
                # POIs with history/architecture/landmark/religious/museum -> "attraction"
                if any(cat in ["history", "architecture", "landmark", "religious", "museum", "archaeology", "science", "viewpoint"] for cat in poi_categories):
                    poi_category = "attraction"
                elif any(cat in ["market", "shopping"] for cat in poi_categories):
                    poi_category = "market"
                elif any(cat in ["food", "restaurant", "cafe"] for cat in poi_categories):
                    poi_category = "restaurant"
                elif any(cat in ["hotel", "accommodation"] for cat in poi_categories):
                    poi_category = "hotel"
                else:
                    poi_category = "attraction"  # default
            else:
                poi_category = "attraction"
            
            # Get image URL - use existing or generate from POI ID
            image_url = poi.get("image_url", "")
            if not image_url:
                # Choose correct image folder based on mapped category
                image_folder = "poi"
                if poi_category == "hotel":
                    image_folder = "hotels"
                elif poi_category == "restaurant":
                    image_folder = "restaurants"
                image_url = get_poi_image_url(poi_id, image_folder)
            
            # #region agent log
            import json
            log_data_poi = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "G",
                "location": "api.py:search_places",
                "message": "POI category mapping",
                "data": {"poi_id": poi_id, "original_categories": poi_categories, "mapped_category": poi_category},
                "timestamp": int(__import__("time").time() * 1000)
            }
            try:
                with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data_poi) + "\n")
            except:
                pass
            # #endregion
            
            places.append({
                "id": poi_id,
                "name": poi.get("name_en") or poi.get("name"),
                "description": poi.get("description", ""),
                "category": poi_category,
                "price": poi.get("cost_usd", 0),
                "rating": poi.get("avg_rating", 4.5),
                "image_url": image_url
            })
    
    # Load restaurants
    hr_path = data_dir / "hotels_restaurants.json"
    if hr_path.exists():
        with open(hr_path, "r", encoding="utf-8") as f:
            hr_data = json.load(f)
        for rest in hr_data.get("restaurants", []):
            # Fix image URL path - change /images/ to /images/ (already correct) or ensure it exists
            image_url = rest.get("image_url", "")
            if image_url and not image_url.startswith("http"):
                # Ensure path starts with /images/ for API serving
                if not image_url.startswith("/images/"):
                    # Extract filename and construct correct path
                    filename = image_url.split("/")[-1]
                    image_url = f"/images/restaurants/{filename}"
            # #region agent log
            import json
            log_data = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "E",
                "location": "api.py:search_places",
                "message": "Restaurant image URL",
                "data": {"rest_id": rest.get("id"), "image_url": image_url, "original": rest.get("image_url", "")},
                "timestamp": int(__import__("time").time() * 1000)
            }
            try:
                with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data) + "\n")
            except:
                pass
            # #endregion
            places.append({
                "id": rest.get("id"),
                "name": rest.get("name"),
                "description": rest.get("description", ""),
                "category": "restaurant",
                "price": rest.get("avg_check_usd", 10),
                "rating": rest.get("rating", 4.0),
                "image_url": image_url
            })
        for hotel in hr_data.get("hotels", []):
            # Fix image URL path
            image_url = hotel.get("image_url", "")
            if image_url and not image_url.startswith("http"):
                # Ensure path starts with /images/ for API serving
                if not image_url.startswith("/images/"):
                    # Extract filename and construct correct path
                    filename = image_url.split("/")[-1]
                    image_url = f"/images/hotels/{filename}"
            # #region agent log
            log_data2 = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "F",
                "location": "api.py:search_places",
                "message": "Hotel image URL",
                "data": {"hotel_id": hotel.get("id"), "image_url": image_url, "original": hotel.get("image_url", "")},
                "timestamp": int(__import__("time").time() * 1000)
            }
            try:
                with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_data2) + "\n")
            except:
                pass
            # #endregion
            places.append({
                "id": hotel.get("id"),
                "name": hotel.get("name"),
                "description": hotel.get("description", ""),
                "category": "hotel",
                "price": hotel.get("price_per_night_usd", 50),
                "rating": hotel.get("rating", 4.0),
                "image_url": image_url
            })
    
    # Filter by category
    if category != "all":
        # #region agent log
        import json
        log_filter = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "H",
            "location": "api.py:search_places",
            "message": "Category filter",
            "data": {"requested_category": category, "places_before_filter": len(places), "place_categories": [p.get("category") for p in places[:5]]},
            "timestamp": int(__import__("time").time() * 1000)
        }
        try:
            with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_filter) + "\n")
        except:
            pass
        # #endregion
        places = [p for p in places if p["category"] == category]
        # #region agent log
        log_filter_after = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "I",
            "location": "api.py:search_places",
            "message": "After category filter",
            "data": {"places_after_filter": len(places)},
            "timestamp": int(__import__("time").time() * 1000)
        }
        try:
            with open("c:\\Users\\hp\\Desktop\\Samarkand_Hacakton\\.cursor\\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_filter_after) + "\n")
        except:
            pass
        # #endregion
    
    # Filter by search query
    if q:
        q_lower = q.lower()
        places = [p for p in places if q_lower in p["name"].lower() or q_lower in p["description"].lower()]
    
    return places[:limit]

@app.get("/v1/map-places")
async def get_map_places():
    """Get places with coordinates for map display."""
    import json
    from pathlib import Path
    
    # Samarkand center coordinates as fallback
    SAMARKAND_CENTER = (39.6548, 66.9758)
    
    places = []
    data_dir = Path(__file__).parent.parent / "data"
    
    # Load POI data
    poi_path = data_dir / "poi.json"
    if poi_path.exists():
        with open(poi_path, "r", encoding="utf-8") as f:
            poi_data = json.load(f)
        for poi in poi_data.get("poi", []):
            coords = poi.get("coordinates", {})
            lat = coords.get("lat", SAMARKAND_CENTER[0])
            lng = coords.get("lng", SAMARKAND_CENTER[1])
            poi_id = poi.get("id")
            poi_categories = poi.get("category", [])
            if isinstance(poi_categories, list):
                if any(cat in ["history", "architecture", "landmark", "religious", "museum", "archaeology", "science", "viewpoint"] for cat in poi_categories):
                    poi_category = "attraction"
                elif any(cat in ["market", "shopping"] for cat in poi_categories):
                    poi_category = "market"
                elif any(cat in ["food", "restaurant", "cafe"] for cat in poi_categories):
                    poi_category = "restaurant"
                elif any(cat in ["hotel", "accommodation"] for cat in poi_categories):
                    poi_category = "hotel"
                else:
                    poi_category = "attraction"
            else:
                poi_category = "attraction"
            image_url = poi.get("image_url", "")
            if not image_url:
                image_folder = "poi"
                if poi_category == "hotel":
                    image_folder = "hotels"
                elif poi_category == "restaurant":
                    image_folder = "restaurants"
                image_url = get_poi_image_url(poi_id, image_folder)
            
            places.append({
                "id": poi_id,
                "name": poi.get("name_en") or poi.get("name"),
                "description": poi.get("description", ""),
                "category": poi_category,
                "type": f"🏛️ {poi_category.title()}",
                "price": f"${poi.get('cost_usd', 0)}",
                "rating": poi.get("avg_rating", 4.5),
                "image_url": image_url,
                "address": "",
                "lat": lat,
                "lng": lng,
                "icon": "🏛️"
            })
    
    hr_path = data_dir / "hotels_restaurants.json"
    if hr_path.exists():
        with open(hr_path, "r", encoding="utf-8") as f:
            hr_data = json.load(f)
        
        # Add restaurants
        for i, rest in enumerate(hr_data.get("restaurants", [])):
            # Get coordinates from JSON or use fallback
            coords = rest.get("coordinates", {})
            lat = coords.get("lat", SAMARKAND_CENTER[0])
            lng = coords.get("lng", SAMARKAND_CENTER[1])
            image_url = rest.get("image_url", "")
            if image_url and not image_url.startswith("http"):
                if not image_url.startswith("/images/"):
                    filename = image_url.split("/")[-1]
                    image_url = f"/images/restaurants/{filename}"
            
            places.append({
                "id": rest.get("id", f"rest_{i}"),
                "name": rest.get("name"),
                "description": rest.get("description", ""),
                "category": "restaurant",
                "type": f"🍽️ {rest.get('category', 'restaurant').replace('-', ' ').title()}",
                "price": f"${rest.get('avg_check_usd', 10)}",
                "rating": rest.get("rating", 4.0),
                "image_url": image_url,
                "address": rest.get("address", ""),
                "lat": lat,
                "lng": lng,
                "icon": "🍽️"
            })
        
        # Add hotels
        for i, hotel in enumerate(hr_data.get("hotels", [])):
            # Get coordinates from JSON or use fallback
            coords = hotel.get("coordinates", {})
            lat = coords.get("lat", SAMARKAND_CENTER[0])
            lng = coords.get("lng", SAMARKAND_CENTER[1])
            image_url = hotel.get("image_url", "")
            if image_url and not image_url.startswith("http"):
                if not image_url.startswith("/images/"):
                    filename = image_url.split("/")[-1]
                    image_url = f"/images/hotels/{filename}"
            
            places.append({
                "id": hotel.get("id", f"hotel_{i}"),
                "name": hotel.get("name"),
                "description": hotel.get("description", ""),
                "category": "hotel",
                "type": f"🏨 {hotel.get('stars', 3)}★ Hotel",
                "price": f"${hotel.get('price_per_night_usd', 50)}/night",
                "rating": hotel.get("rating", 4.0),
                "image_url": image_url,
                "address": hotel.get("address", ""),
                "lat": lat,
                "lng": lng,
                "icon": "🏨"
            })
    
    return {"places": places}

@app.post("/v1/ask-ai")
async def ask_ai(request: ChatRequest):
    """Ask the AI any travel question."""
    llm = get_llm()
    
    system = "You are SaFar, an AI travel expert for Samarkand, Uzbekistan. Answer travel questions helpfully and concisely. IMPORTANT: Respond in the same language as the user's message (English, Russian, or Uzbek)."
    
    try:
        response = llm.complete(request.message, system_prompt=system)
        return {"answer": response}
    except Exception as e:
        return {"answer": f"Sorry, I couldn't process that: {str(e)}"}

@app.post("/v1/context-chat")
async def context_chat(request: ChatRequest):
    """Ask contextual questions (transport, currency, etc)."""
    agent = get_context_chat()
    result = agent.answer(request.message)
    return result

@app.post("/v1/story")
async def tell_story(request: StoryRequest):
    """Generate a story about a place."""
    agent = get_storyteller()
    return agent.tell_story(request.poi_id, request.language, request.style)

@app.get("/v1/weather")
async def get_weather_forecast(days: int = 3):
    """Get weather forecast."""
    service = get_weather()
    forecasts = await service.get_forecast(days)
    return {"forecasts": forecasts}

# --- Run ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
