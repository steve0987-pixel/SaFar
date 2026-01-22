"""
Hybrid RAG Retriever - Metadata Filters + Semantic Search.
Combines deterministic filtering with embedding-based similarity.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.schemas import POI, TripRequest, RetrievalResult, PhysicalLevel


@dataclass
class FilterCriteria:
    """Metadata filter criteria for deterministic filtering."""
    city: str = "Samarkand"
    categories: List[str] = None
    max_cost_usd: float = None
    max_duration_hours: float = None
    physical_level: str = None
    required_tags: List[str] = None
    exclude_tags: List[str] = None
    day_specific: int = None  # For constraints like "mountains on day 2"


class HybridPOIRetriever:
    """
    Hybrid RAG retriever combining:
    1. Metadata filters (deterministic) - guarantees constraint satisfaction
    2. Semantic search (embeddings) - provides smart relevance ranking
    
    This ensures:
    - Filters guarantee constraints are met
    - Embeddings provide intelligent matching
    - Results are stable and reproducible
    """
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or str(Path(__file__).parent.parent.parent / "data" / "poi.json")
        self.pois: Dict[str, POI] = {}
        self.poi_texts: Dict[str, str] = {}  # For semantic search
        
        # Embedding model
        self.embedder = None
        self.poi_embeddings: Dict[str, list] = {}
        
        # ChromaDB collection
        self.collection = None
        self.use_vectors = False
        
        self._load_data()
        self._init_embeddings()
    
    def _load_data(self):
        """Load POI data from JSON file."""
        try:
            # Load basic POIs
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for poi_data in data.get("poi", []):
                poi = POI.model_validate(poi_data)
                self.pois[poi.id] = poi
                self.poi_texts[poi.id] = self._create_searchable_text(poi)
            
            # Load Hotels and Restaurants
            extra_path = str(Path(self.data_path).parent / "hotels_restaurants.json")
            if Path(extra_path).exists():
                try:
                    with open(extra_path, "r", encoding="utf-8") as f:
                        extra_data = json.load(f)
                    
                    # Process Restaurants
                    for rest_data in extra_data.get("restaurants", []):
                        poi = self._convert_restaurant_to_poi(rest_data)
                        self.pois[poi.id] = poi
                        self.poi_texts[poi.id] = self._create_searchable_text(poi)
                        
                    # Process Hotels
                    for hotel_data in extra_data.get("hotels", []):
                        poi = self._convert_hotel_to_poi(hotel_data)
                        self.pois[poi.id] = poi
                        self.poi_texts[poi.id] = self._create_searchable_text(poi)
                        
                    print(f"   Loaded extra {len(extra_data.get('restaurants', []))} restaurants and {len(extra_data.get('hotels', []))} hotels")
                except Exception as e:
                    print(f"⚠️  Error loading extra data: {e}")
            
            
            print(f"✅ Loaded {len(self.pois)} POIs")
        except Exception as e:
            print(f"⚠️  Error loading POI data: {e}")
    def _convert_restaurant_to_poi(self, data: dict) -> POI:
        """Convert restaurant data to POI."""
        tags = ["restaurant", "food"] + data.get("features", []) + data.get("cuisine", [])
        tags.append(data.get("category", "casual"))
        tags.append(data.get("price_range", "$"))
        
        return POI(
            id=data["id"],
            name=data["name"],
            name_en=data.get("name_uz"), # Storing UZ name in name_en for now or leave distinct
            category=["food", "restaurant"],
            description=data["description"] + f" Specialties: {', '.join(data.get('specialties', []))}",
            cost_usd=data.get("avg_check_usd", 10),
            duration_hours=1.5,
            best_time="lunch" if "lunch" in str(data) else "dinner",
            opening_hours=data.get("opening_hours"),
            coordinates=data.get("coordinates"),
            tags=[t.lower().replace(" ", "-") for t in tags],
            tips=[f"Avg check: ${data.get('avg_check_usd')}", f"Rating: {data.get('rating')}/5"],
            physical_level="low"
        )

    def _convert_hotel_to_poi(self, data: dict) -> POI:
        """Convert hotel data to POI."""
        tags = ["hotel", "accommodation"] + data.get("amenities", [])
        tags.append(f"{data.get('stars', 3)}-star")
        tags.append(data.get("category", "standard"))
        
        return POI(
            id=data["id"],
            name=data["name"],
            category=["hotel", "accommodation"],
            description=data["description"],
            cost_usd=data.get("price_per_night_usd", 50), # Storing nightly rate
            duration_hours=0, # Hotels are stays, not activities
            best_time="any",
            district="center", # default
            coordinates=data.get("coordinates"),
            tags=[t.lower().replace(" ", "-") for t in tags],
            tips=[f"Price: ${data.get('price_per_night_usd')}/night", f"Rating: {data.get('rating')}/5"],
            physical_level="low"
        )


    def _create_searchable_text(self, poi: POI) -> str:
        """Create rich text representation for semantic search."""
        parts = [
            poi.name,
            poi.name_en or "",
            poi.description,
            " ".join(poi.category),
            " ".join(poi.tags),
            poi.district,
            " ".join(poi.tips) if poi.tips else ""
        ]
        return " ".join(filter(None, parts))
    
    def _init_embeddings(self):
        """Initialize embedding model and index POIs."""
        try:
            import chromadb
            
            # Create persistent client
            self.chroma_client = chromadb.Client()
            
            # Create collection with embedding function
            self.collection = self.chroma_client.get_or_create_collection(
                name="samarkand_poi_hybrid",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Index POIs if collection is empty
            if self.collection.count() == 0:
                self._index_pois()
            
            self.use_vectors = True
            print(f"✅ Vector store ready with {self.collection.count()} embeddings")
            
        except ImportError:
            print("⚠️  ChromaDB not installed. Using keyword-based fallback.")
            print("   pip install chromadb sentence-transformers")
            self.use_vectors = False
        except Exception as e:
            print(f"⚠️  Error initializing embeddings: {e}")
            self.use_vectors = False
    
    def _index_pois(self):
        """Index all POIs with rich metadata."""
        if not self.collection:
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for poi_id, poi in self.pois.items():
            documents.append(self.poi_texts[poi_id])
            
            metadatas.append({
                "name": poi.name,
                "categories": ",".join(poi.category),
                "cost_usd": poi.cost_usd,
                "duration_hours": poi.duration_hours,
                "physical_level": poi.physical_level.value if hasattr(poi.physical_level, 'value') else str(poi.physical_level),
                "tags": ",".join(poi.tags),
                "district": poi.district,
                "best_time": poi.best_time,
                "is_mountain": "true" if any(t in poi.tags for t in ["mountains", "day2_mountains", "nature", "trekking"]) else "false",
                "is_must_see": "true" if "must-see" in poi.tags else "false"
            })
            
            ids.append(poi_id)
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"   Indexed {len(documents)} POIs with metadata")
    
    def search(
        self,
        query: str = None,
        trip_request: TripRequest = None,
        filters: FilterCriteria = None,
        top_k: int = 15
    ) -> List[RetrievalResult]:
        """
        Hybrid search: Metadata filters + Semantic ranking.
        
        Steps:
        1. Build filters from TripRequest constraints
        2. Apply deterministic metadata filters
        3. Rank filtered results by semantic similarity
        4. Return top-k
        """
        
        # Step 1: Build filter criteria from trip request
        if trip_request and not filters:
            filters = self._build_filters_from_request(trip_request)
        
        # Step 2: Build semantic query
        if not query and trip_request:
            query = self._build_semantic_query(trip_request)
        
        if not query:
            query = "достопримечательности Самарканд"
        
        # Step 3: Execute search
        if self.use_vectors and self.collection:
            return self._hybrid_search(query, filters, top_k)
        else:
            return self._keyword_search(query, filters, top_k)
    
    def _build_filters_from_request(self, request: TripRequest) -> FilterCriteria:
        """Extract filter criteria from TripRequest."""
        
        filters = FilterCriteria(city=request.city)
        
        # Budget constraint
        avg_daily_budget = request.budget_usd / request.duration_days
        filters.max_cost_usd = avg_daily_budget * 0.3  # Max 30% on single POI
        
        # Categories from interests
        if request.interests:
            filters.categories = request.interests.copy()
        
        # Physical level
        filters.physical_level = request.physical_level.value if hasattr(request.physical_level, 'value') else str(request.physical_level)
        
        # Check for day-specific mountain constraint
        for constraint in request.constraints:
            c_lower = constraint.lower()
            if "mountain" in c_lower or "гор" in c_lower:
                # Find which day
                for i in range(1, 10):
                    if str(i) in constraint:
                        filters.day_specific = i
                        filters.required_tags = ["day2_mountains", "mountains", "nature"]
                        break
        
        return filters
    
    def _build_semantic_query(self, request: TripRequest) -> str:
        """Build semantic query from trip request."""
        
        parts = []
        
        # Add interests
        parts.extend(request.interests)
        
        # Add constraint keywords
        for constraint in request.constraints:
            # Extract meaningful words
            words = constraint.lower().replace(",", " ").split()
            parts.extend([w for w in words if len(w) > 3])
        
        # Add city
        parts.append(request.city)
        
        return " ".join(parts)
    
    def _hybrid_search(
        self,
        query: str,
        filters: FilterCriteria,
        top_k: int
    ) -> List[RetrievalResult]:
        """Hybrid search using ChromaDB with metadata filters."""
        
        # Build ChromaDB where filter
        where_filter = {}
        
        if filters:
            where_conditions = []
            
            if filters.max_cost_usd is not None:
                where_conditions.append({"cost_usd": {"$lte": filters.max_cost_usd}})
            
            if filters.required_tags:
                # Search for mountain-related content
                where_conditions.append({"is_mountain": "true"})
            
            if len(where_conditions) == 1:
                where_filter = where_conditions[0]
            elif len(where_conditions) > 1:
                where_filter = {"$and": where_conditions}
        
        # Semantic search with filters
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k * 2, 30),  # Get more for post-filtering
                where=where_filter if where_filter else None
            )
        except Exception as e:
            print(f"⚠️  ChromaDB query error: {e}")
            # Fallback to unfiltered search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k * 2
            )
        
        # Convert to RetrievalResults
        retrieval_results = []
        
        if results and results["ids"] and results["ids"][0]:
            for i, poi_id in enumerate(results["ids"][0]):
                if poi_id not in self.pois:
                    continue
                
                poi = self.pois[poi_id]
                
                # Additional post-filtering
                if filters:
                    if not self._passes_filters(poi, filters):
                        continue
                
                # Calculate score (ChromaDB returns distances, convert to similarity)
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1.0 / (1.0 + distance)  # Convert distance to similarity
                
                # Boost scores
                score = self._apply_score_boosts(poi, score, filters)
                
                retrieval_results.append(RetrievalResult(
                    poi=poi,
                    score=min(1.0, score),
                    matched_tags=self._get_matched_tags(poi, query)
                ))
        
        # Sort by score and limit
        retrieval_results.sort(key=lambda x: x.score, reverse=True)
        return retrieval_results[:top_k]
    
    def _keyword_search(
        self,
        query: str,
        filters: FilterCriteria,
        top_k: int
    ) -> List[RetrievalResult]:
        """Fallback keyword-based search with filtering."""
        
        query_terms = set(query.lower().split())
        results = []
        
        for poi_id, poi in self.pois.items():
            # Apply filters first (deterministic)
            if filters and not self._passes_filters(poi, filters):
                continue
            
            # Calculate relevance score
            score = 0
            poi_text = self.poi_texts[poi_id].lower()
            poi_tags = set([t.lower() for t in poi.tags + poi.category])
            
            # Match query terms
            for term in query_terms:
                if term in poi_text:
                    score += 0.2
                if term in poi_tags:
                    score += 0.4
                if term in poi.name.lower():
                    score += 0.3
            
            # Apply boosts
            score = self._apply_score_boosts(poi, score, filters)
            
            if score > 0:
                results.append(RetrievalResult(
                    poi=poi,
                    score=min(1.0, score),
                    matched_tags=self._get_matched_tags(poi, query)
                ))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _passes_filters(self, poi: POI, filters: FilterCriteria) -> bool:
        """Check if POI passes all deterministic filters."""
        
        # Cost filter
        if filters.max_cost_usd is not None and poi.cost_usd > filters.max_cost_usd:
            return False
        
        # Duration filter
        if filters.max_duration_hours is not None and poi.duration_hours > filters.max_duration_hours:
            return False
        
        # Category filter (must match at least one if specified)
        if filters.categories:
            if not any(cat in poi.category for cat in filters.categories):
                # Allow if POI has general interest tags
                if not any(cat in poi.tags for cat in filters.categories):
                    pass  # Don't strictly filter, just lower score
        
        # Exclude tags
        if filters.exclude_tags:
            if any(tag in poi.tags for tag in filters.exclude_tags):
                return False
        
        return True
    
    def _apply_score_boosts(
        self,
        poi: POI,
        base_score: float,
        filters: FilterCriteria
    ) -> float:
        """Apply score boosts based on relevance signals."""
        
        score = base_score
        
        # Must-see boost
        if "must-see" in poi.tags:
            score += 0.3
        
        # UNESCO boost
        if "unesco" in poi.tags:
            score += 0.2
        
        # Free entry boost for budget
        if poi.cost_usd == 0:
            score += 0.1
        
        # Mountain boost if required
        if filters and filters.required_tags:
            mountain_tags = ["mountains", "day2_mountains", "nature", "trekking", "hiking"]
            if any(tag in poi.tags for tag in mountain_tags):
                score += 0.5
        
        # Photography boost
        if "photography" in poi.tags:
            score += 0.1
        
        return score
    
    def _get_matched_tags(self, poi: POI, query: str) -> List[str]:
        """Get list of tags that matched the query."""
        query_terms = set(query.lower().split())
        matched = []
        
        for tag in poi.tags:
            if any(term in tag.lower() for term in query_terms):
                matched.append(tag)
        
        return matched
    
    # Convenience methods
    
    def get_by_id(self, poi_id: str) -> Optional[POI]:
        """Get POI by ID or by name (fuzzy match)."""
        # Try exact ID match first
        if poi_id in self.pois:
            return self.pois[poi_id]
        
        # Try normalized ID (lowercase, underscores)
        normalized_id = poi_id.lower().replace("-", "_").replace(" ", "_")
        for pid, poi in self.pois.items():
            if pid.lower().replace("-", "_") == normalized_id:
                return poi
        
        # Try name-based search (for frontend-generated IDs)
        search_terms = normalized_id.replace("_", " ").split()
        for poi in self.pois.values():
            poi_name_lower = poi.name.lower()
            # Check if all search terms appear in the name
            if all(term in poi_name_lower for term in search_terms if len(term) > 2):
                return poi
            # Also check English name
            if poi.name_en and all(term in poi.name_en.lower() for term in search_terms if len(term) > 2):
                return poi
        
        return None
    
    def get_by_tag(self, tag: str) -> List[POI]:
        """Get all POIs with specific tag."""
        return [poi for poi in self.pois.values() if tag in poi.tags]
    
    def get_mountain_options(self) -> List[POI]:
        """Get POIs suitable for mountain day trips."""
        mountain_tags = ["day2_mountains", "mountains", "nature", "trekking"]
        results = []
        
        for poi in self.pois.values():
            if any(tag in poi.tags for tag in mountain_tags):
                if poi.duration_hours >= 4:  # Full day activities
                    results.append(poi)
        
        return sorted(results, key=lambda x: -x.duration_hours)
    
    def get_must_see(self) -> List[POI]:
        """Get must-see POIs."""
        return self.get_by_tag("must-see")
    
    def get_by_category(self, category: str) -> List[POI]:
        """Get POIs by category."""
        return [poi for poi in self.pois.values() if category in poi.category]
    
    def get_all(self) -> List[POI]:
        """Get all POIs."""
        return list(self.pois.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the POI database."""
        categories = {}
        total_cost = 0
        
        for poi in self.pois.values():
            for cat in poi.category:
                categories[cat] = categories.get(cat, 0) + 1
            total_cost += poi.cost_usd
        
        return {
            "total_pois": len(self.pois),
            "categories": categories,
            "avg_cost": total_cost / len(self.pois) if self.pois else 0,
            "must_see_count": len(self.get_must_see()),
            "mountain_options": len(self.get_mountain_options()),
            "vectors_enabled": self.use_vectors
        }


class TipsRetriever:
    """Retriever for tips and recommendations."""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or str(Path(__file__).parent.parent.parent / "data" / "tips.json")
        self.tips: Dict[str, List[str]] = {}
        self.seasonal: Dict[str, str] = {}
        self._load_data()
    
    def _load_data(self):
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.tips = data.get("categories", {})
            self.seasonal = data.get("seasonal", {})
            
            print(f"✅ Loaded tips for {len(self.tips)} categories")
        except Exception as e:
            print(f"⚠️  Error loading tips: {e}")
    
    def get_tips(self, category: str) -> List[str]:
        return self.tips.get(category, [])
    
    def get_relevant_tips(self, trip_request: TripRequest) -> List[str]:
        """Get tips relevant to the trip request."""
        relevant = []
        
        # General tips
        relevant.extend(self.tips.get("general", [])[:2])
        
        # Budget tips
        if trip_request.budget_usd < 80:
            relevant.extend(self.tips.get("budget", [])[:2])
        
        # Mountain tips
        has_mountain = any(
            "mountain" in c.lower() or "гор" in c.lower() 
            for c in trip_request.constraints
        )
        if has_mountain or "nature" in trip_request.interests:
            relevant.extend(self.tips.get("mountains", []))
        
        # Photography tips
        if "photography" in trip_request.interests:
            relevant.extend(self.tips.get("photography", [])[:2])
        
        # Food tips
        if "food" in trip_request.interests:
            relevant.extend(self.tips.get("food", [])[:2])
        
        return relevant


# Backward compatibility alias
POIRetriever = HybridPOIRetriever


# Quick test
if __name__ == "__main__":
    retriever = HybridPOIRetriever()
    
    print("\n📊 Database stats:")
    stats = retriever.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n🔍 Hybrid search: 'history architecture'")
    results = retriever.search("history architecture Регистан", top_k=5)
    for r in results:
        print(f"   [{r.score:.2f}] {r.poi.name} - ${r.poi.cost_usd}")
    
    print("\n🏔️ Mountain options:")
    mountains = retriever.get_mountain_options()
    for m in mountains:
        print(f"   {m.name} - ${m.cost_usd}, {m.duration_hours}h")
    
    print("\n⭐ Must-see POIs:")
    must_see = retriever.get_must_see()
    for p in must_see[:5]:
        print(f"   {p.name}")
