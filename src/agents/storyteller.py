"""
Culture Storyteller Agent - Generates engaging stories about Samarkand's places.
Uses RAG to enhance narratives with historical facts, legends, and local lore.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.llm import get_llm_client
from src.rag.retriever import HybridPOIRetriever


# Pre-built story elements for main attractions
STORY_ELEMENTS = {
    "registan": {
        "legends": [
            "По легенде, Тамерлан приказал построить медресе так, чтобы они касались неба",
            "Говорят, что звёзды на куполах отражают реальную карту неба 15 века"
        ],
        "facts": [
            "Площадь была центром империи Тимуридов",
            "Три медресе строились с 1417 по 1660 год",
            "Название означает 'песчаное место'"
        ],
        "atmosphere": "закат окрашивает майолику в золото, а ночная подсветка создаёт магическую атмосферу"
    },
    "gur_emir": {
        "legends": [
            "Существует проклятие: 'Кто откроет мою гробницу, развяжет войну страшнее меня'",
            "Гробницу вскрыли 22 июня 1941 года — в день начала войны с Германией"
        ],
        "facts": [
            "Здесь покоится Тамерлан (Амир Темур) и его потомки",
            "Нефритовый надгробный камень — один из крупнейших в мире",
            "Купол высотой 12.5 метров покрыт небесно-голубой плиткой"
        ],
        "atmosphere": "тишина и величие, ощущение связи с великой историей"
    },
    "shah_i_zinda": {
        "legends": [
            "Кусам ибн Аббас, двоюродный брат Пророка, был обезглавлен, но взял свою голову и ушёл в колодец, где живёт до сих пор",
            "Отсюда название — 'Живой Царь'"
        ],
        "facts": [
            "Некрополь строился с 11 по 19 век",
            "Здесь 44 мавзолея с уникальной майоликой",
            "Самые красивые образцы тимуридской керамики в мире"
        ],
        "atmosphere": "узкие улочки между мавзолеями создают ощущение путешествия во времени"
    }
}


class CultureStoryteller:
    """
    AI-powered storyteller that creates engaging narratives about Samarkand's places.
    Combines historical facts, legends, and atmospheric descriptions.
    """
    
    STORY_PROMPT = """You are a master storyteller and historian of Samarkand, 
the ancient city on the Silk Road. Create an engaging, immersive story about {poi_name}.

Background information:
{context}

Requirements:
1. Start with a captivating hook
2. Weave historical facts naturally into the narrative
3. Include at least one legend or mystery
4. Describe the atmosphere and sensory details
5. End with something memorable for the visitor

Style: Evocative, rich but not academic. Make the reader feel they're there.
Length: 2-3 paragraphs (150-250 words)
Language: {language}

Create the story:
"""

    QUICK_STORY_PROMPT = """Create a brief (2-3 sentences) intriguing teaser about {poi_name} 
that makes tourists want to visit. Include one interesting fact or legend.
Language: {language}
"""

    def __init__(self, llm_client=None, poi_retriever=None):
        self.llm = llm_client or get_llm_client()
        self.poi_retriever = poi_retriever or HybridPOIRetriever()
    
    def tell_story(
        self, 
        poi_id: str, 
        language: str = "ru",
        style: str = "full"  # "full", "brief", "legend"
    ) -> Dict:
        """
        Generate an engaging story about a POI.
        
        Args:
            poi_id: ID of the place
            language: Output language (ru, en, uz)
            style: Story style - full, brief, or legend-focused
        
        Returns:
            dict with story and metadata
        """
        
        # 1. Get POI data
        poi = self.poi_retriever.get_by_id(poi_id)
        if not poi:
            return {"story": "Место не найдено", "success": False}
        
        # 2. Get pre-built elements if available
        poi_key = poi_id.lower().replace("-", "_").replace(" ", "_")
        elements = STORY_ELEMENTS.get(poi_key, {})
        
        # 3. Build context
        context = self._build_context(poi, elements)
        
        # 4. Generate story
        if style == "brief":
            prompt = self.QUICK_STORY_PROMPT.format(
                poi_name=poi.name,
                language=language
            )
        else:
            prompt = self.STORY_PROMPT.format(
                poi_name=poi.name,
                context=context,
                language=language
            )
        
        try:
            story = self.llm.complete(prompt)
            
            return {
                "story": story,
                "poi_name": poi.name,
                "style": style,
                "has_legend": bool(elements.get("legends")),
                "success": True
            }
        except Exception as e:
            # Fallback to pre-built content
            return self._fallback_story(poi, elements, language)
    
    def _build_context(self, poi, elements: Dict) -> str:
        """Build context string from POI data and story elements."""
        
        parts = []
        
        # POI description
        parts.append(f"Description: {poi.description}")
        
        # Category and tags
        parts.append(f"Categories: {', '.join(poi.category)}")
        if poi.tags:
            parts.append(f"Tags: {', '.join(poi.tags)}")
        
        # Tips
        if poi.tips:
            parts.append(f"Visitor tips: {'; '.join(poi.tips[:2])}")
        
        # Pre-built story elements
        if elements.get("legends"):
            parts.append(f"Legends: {'; '.join(elements['legends'])}")
        if elements.get("facts"):
            parts.append(f"Facts: {'; '.join(elements['facts'])}")
        if elements.get("atmosphere"):
            parts.append(f"Atmosphere: {elements['atmosphere']}")
        
        return "\n".join(parts)
    
    def _fallback_story(self, poi, elements: Dict, language: str) -> Dict:
        """Generate a fallback story without LLM."""
        
        # Build a simple story from available data
        story_parts = []
        
        # Opening with description
        story_parts.append(poi.description)
        
        # Add a legend if available
        if elements.get("legends"):
            story_parts.append(f"\n\n🔮 Легенда: {elements['legends'][0]}")
        
        # Add atmosphere
        if elements.get("atmosphere"):
            story_parts.append(f"\n\n✨ {elements['atmosphere'].capitalize()}")
        
        # Add tip
        if poi.tips:
            story_parts.append(f"\n\n💡 Совет: {poi.tips[0]}")
        
        return {
            "story": "".join(story_parts),
            "poi_name": poi.name,
            "style": "fallback",
            "success": True
        }
    
    def get_legend(self, poi_id: str) -> Optional[str]:
        """Get just the legend for a POI."""
        
        poi_key = poi_id.lower().replace("-", "_").replace(" ", "_")
        elements = STORY_ELEMENTS.get(poi_key, {})
        
        legends = elements.get("legends", [])
        if legends:
            return legends[0]
        
        return None
    
    def get_atmosphere(self, poi_id: str) -> Optional[str]:
        """Get atmospheric description for a POI."""
        
        poi_key = poi_id.lower().replace("-", "_").replace(" ", "_")
        elements = STORY_ELEMENTS.get(poi_key, {})
        
        return elements.get("atmosphere")


# Quick test
if __name__ == "__main__":
    storyteller = CultureStoryteller()
    
    test_pois = ["registan", "gur_emir", "shah_i_zinda"]
    
    for poi_id in test_pois:
        print(f"\n{'='*60}")
        print(f"📖 История: {poi_id}")
        print("="*60)
        
        result = storyteller.tell_story(poi_id, language="ru", style="full")
        print(result["story"])
        
        legend = storyteller.get_legend(poi_id)
        if legend:
            print(f"\n🔮 Легенда: {legend}")
