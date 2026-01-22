"""
Context Chat Agent - Answers practical travel questions during the trip.
Provides contextual help about transportation, currency, emergency contacts, etc.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.llm import get_llm_client
from src.rag.retriever import HybridPOIRetriever, TipsRetriever


# Knowledge base for common questions
LOCAL_KNOWLEDGE = {
    "emergency": {
        "police": "102",
        "ambulance": "103",
        "fire": "101",
        "tourist_police": "+998 66 233 00 07"
    },
    "currency": {
        "name": "Uzbek Sum (UZS)",
        "rate_info": "~12,500 UZS = 1 USD (январь 2026)",
        "exchange_places": [
            "Banks: Обмен с паспортом, лучший курс",
            "Обменники: На базарах и в центре",
            "ATM: Есть Visa/Mastercard банкоматы"
        ]
    },
    "transport": {
        "taxi": {
            "yandex_go": "Самый удобный, оплата картой",
            "local_taxi": "Торгуйтесь! Обычно 10-20k UZS по городу",
            "tip": "Договаривайтесь о цене заранее"
        },
        "bus": "Маршрутки 1500-2000 UZS, автобусы 1400 UZS"
    },
    "useful_phrases": {
        "hello": "Assalomu alaykum (Ассалому алейкум)",
        "thank_you": "Rahmat (Рахмат)",
        "how_much": "Qancha? (Канча?)",
        "too_expensive": "Qimmat (Киммат)"
    }
}


class ContextChatAgent:
    """
    AI-powered contextual assistant for tourists in Samarkand.
    Answers practical questions using RAG + LLM + local knowledge base.
    """
    
    SYSTEM_PROMPT = """You are SaFar Assistant, a helpful travel AI for tourists 
currently visiting Samarkand, Uzbekistan.

Answer questions about:
- Transportation (taxi, bus, train)
- Currency exchange and payments
- Emergency contacts
- Local customs and etiquette
- Navigation and directions
- Restaurant and shop recommendations
- Opening hours and prices
- Safety tips

Rules:
1. Be concise but helpful
2. Provide specific, actionable information
3. Include relevant local tips
4. Respond in the same language as the question
5. If unsure, say so honestly
6. IMPORTANT: Always answer in the language of the user's question (English, Russian, or Uzbek).
"""

    CONTEXT_TEMPLATE = """
Local Knowledge:
{local_context}

Nearby Places:
{nearby_pois}

Relevant Tips:
{tips}

User Question: {question}

Answer helpfully and concisely:
"""

    def __init__(self, llm_client=None, poi_retriever=None, tips_retriever=None):
        self.llm = llm_client or get_llm_client()
        self.poi_retriever = poi_retriever or HybridPOIRetriever()
        self.tips_retriever = tips_retriever or TipsRetriever()
    
    def answer(
        self, 
        question: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Answer a user question with context.
        
        Args:
            question: User's question
            user_context: Optional context (current_poi, language, etc.)
        
        Returns:
            dict with answer and metadata
        """
        
        # 1. Check for quick answers from knowledge base
        quick_answer = self._check_knowledge_base(question)
        if quick_answer:
            return {
                "answer": quick_answer,
                "source": "knowledge_base",
                "confidence": 0.95
            }
        
        # 2. Get relevant context from RAG
        local_context = self._get_local_context(question)
        nearby_pois = self._get_nearby_pois(question, user_context)
        tips = self._get_relevant_tips(question)
        
        # 3. Build prompt with context
        prompt = self.CONTEXT_TEMPLATE.format(
            local_context=local_context,
            nearby_pois=nearby_pois,
            tips=tips,
            question=question
        )
        
        # 4. Get LLM response
        try:
            response = self.llm.complete(prompt, system_prompt=self.SYSTEM_PROMPT)
            return {
                "answer": response,
                "source": "ai",
                "confidence": 0.85,
                "context_used": bool(nearby_pois or tips)
            }
        except Exception as e:
            return {
                "answer": f"Извините, не могу ответить на этот вопрос. Попробуйте переформулировать. Ошибка: {str(e)}",
                "source": "error",
                "confidence": 0.0
            }
    
    def _check_knowledge_base(self, question: str) -> Optional[str]:
        """Check if question can be answered from local knowledge base."""
        
        q_lower = question.lower()
        
        # Emergency
        if any(word in q_lower for word in ["скорая", "полиция", "пожар", "emergency", "помощь", "urgent"]):
            info = LOCAL_KNOWLEDGE["emergency"]
            return f"📞 Экстренные номера:\n• Полиция: {info['police']}\n• Скорая: {info['ambulance']}\n• Пожарные: {info['fire']}\n• Туристическая полиция: {info['tourist_police']}"
        
        # Currency
        if any(word in q_lower for word in ["обмен", "валют", "курс", "доллар", "сум", "currency", "exchange", "money"]):
            info = LOCAL_KNOWLEDGE["currency"]
            places = "\n".join(f"• {p}" for p in info["exchange_places"])
            return f"💰 Валюта: {info['name']}\nПримерный курс: {info['rate_info']}\n\nГде обменять:\n{places}"
        
        # Taxi
        if any(word in q_lower for word in ["такси", "taxi", "доехать", "транспорт"]):
            info = LOCAL_KNOWLEDGE["transport"]["taxi"]
            return f"🚕 Такси в Самарканде:\n• Yandex Go: {info['yandex_go']}\n• Местные такси: {info['local_taxi']}\n💡 Совет: {info['tip']}"
        
        # Phrases
        if any(word in q_lower for word in ["фраз", "слов", "узбек", "phrase", "word"]):
            phrases = LOCAL_KNOWLEDGE["useful_phrases"]
            return f"🗣️ Полезные фразы:\n• Привет: {phrases['hello']}\n• Спасибо: {phrases['thank_you']}\n• Сколько?: {phrases['how_much']}\n• Дорого: {phrases['too_expensive']}"
        
        return None
    
    def _get_local_context(self, question: str) -> str:
        """Get relevant local context for the question."""
        
        # Check question topic
        if "регистан" in question.lower():
            return "Registan Square: открыт 08:00-20:00, вход $5, лучшее время для фото - закат"
        elif "плов" in question.lower() or "plov" in question.lower():
            return "Лучший плов: Boss Plov (рядом с Siab Bazaar), подают до 13:00"
        elif "базар" in question.lower() or "рынок" in question.lower():
            return "Siab Bazaar: открыт 06:00-18:00, лучшие цены утром, торгуйтесь!"
        
        return ""
    
    def _get_nearby_pois(self, question: str, user_context: Optional[Dict] = None) -> str:
        """Get nearby POIs relevant to the question."""
        
        try:
            results = self.poi_retriever.search(query=question, top_k=3)
            if results:
                pois = [f"• {r.poi.name}: {r.poi.description[:50]}..." for r in results[:3]]
                return "\n".join(pois)
        except:
            pass
        
        return ""
    
    def _get_relevant_tips(self, question: str) -> str:
        """Get relevant tips from tips retriever."""
        
        try:
            # Map question to tip category
            q_lower = question.lower()
            
            if any(w in q_lower for w in ["еда", "есть", "ресторан", "food"]):
                tips = self.tips_retriever.get_tips("food")
            elif any(w in q_lower for w in ["покуп", "магазин", "сувенир", "shop"]):
                tips = self.tips_retriever.get_tips("shopping") 
            elif any(w in q_lower for w in ["безопас", "совет", "safety"]):
                tips = self.tips_retriever.get_tips("safety")
            else:
                tips = self.tips_retriever.get_tips("general")
            
            if tips:
                return "\n".join(f"• {t}" for t in tips[:3])
        except:
            pass
        
        return ""


# Quick test
if __name__ == "__main__":
    agent = ContextChatAgent()
    
    test_questions = [
        "Где обменять доллары?",
        "Как вызвать такси?",
        "Номер скорой помощи?",
        "Где лучший плов в Самарканде?",
        "Как сказать спасибо по-узбекски?"
    ]
    
    for q in test_questions:
        print(f"\n❓ {q}")
        result = agent.answer(q)
        print(f"💬 {result['answer']}")
        print(f"   [источник: {result['source']}, уверенность: {result['confidence']:.0%}]")
