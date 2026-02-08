"""
Data Validator for SaFar Trip Planner.
Validates POI and restaurant data at startup.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    """Single validation issue."""
    severity: str  # "error", "warning"
    item_id: str
    item_type: str  # "poi", "restaurant", "hotel"
    field: str
    message: str


@dataclass
class ValidationResult:
    """Complete validation result."""
    is_valid: bool = True
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    
    def add_error(self, item_id: str, item_type: str, field: str, message: str):
        self.errors.append(ValidationIssue("error", item_id, item_type, field, message))
        self.is_valid = False
    
    def add_warning(self, item_id: str, item_type: str, field: str, message: str):
        self.warnings.append(ValidationIssue("warning", item_id, item_type, field, message))
    
    def summary(self) -> str:
        lines = []
        if self.is_valid:
            lines.append("✅ Data validation PASSED")
        else:
            lines.append("❌ Data validation FAILED")
        
        lines.append(f"   Errors: {len(self.errors)}, Warnings: {len(self.warnings)}")
        
        for issue in self.errors[:10]:  # Show first 10 errors
            lines.append(f"   ❌ [{issue.item_type}] {issue.item_id}.{issue.field}: {issue.message}")
        
        for issue in self.warnings[:5]:  # Show first 5 warnings
            lines.append(f"   ⚠️ [{issue.item_type}] {issue.item_id}.{issue.field}: {issue.message}")
        
        return "\n".join(lines)


class DataValidator:
    """Validates POI and restaurant data."""
    
    # Samarkand bounding box (approximate)
    SAMARKAND_BOUNDS = {
        "lat_min": 39.55,
        "lat_max": 39.75,
        "lng_min": 66.85,
        "lng_max": 67.10
    }
    
    TIME_PATTERN = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)$')
    HOURS_PATTERN = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)-([01]?\d|2[0-3]):([0-5]\d)$')
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "database"
        self.data_dir = data_dir
        self.poi_data: Dict[str, Any] = {}
        self.hr_data: Dict[str, Any] = {}
        
    def load_data(self) -> bool:
        """Load data files. Returns True if successful."""
        poi_path = self.data_dir / "poi.json"
        hr_path = self.data_dir / "hotels_restaurants.json"
        
        try:
            if poi_path.exists():
                with open(poi_path, "r", encoding="utf-8") as f:
                    self.poi_data = json.load(f)
            
            if hr_path.exists():
                with open(hr_path, "r", encoding="utf-8") as f:
                    self.hr_data = json.load(f)
            
            return True
        except Exception as e:
            print(f"❌ Failed to load data: {e}")
            return False
    
    def validate_all(self) -> ValidationResult:
        """Run all validations and return result."""
        result = ValidationResult()
        
        if not self.load_data():
            result.add_error("system", "system", "load", "Failed to load data files")
            return result
        
        # Collect all IDs for uniqueness check
        all_ids: Set[str] = set()
        
        # Validate POI
        for poi in self.poi_data.get("poi", []):
            self._validate_poi(poi, result, all_ids)
        
        # Validate restaurants
        for rest in self.hr_data.get("restaurants", []):
            self._validate_restaurant(rest, result, all_ids)
        
        # Validate hotels
        for hotel in self.hr_data.get("hotels", []):
            self._validate_hotel(hotel, result, all_ids)
        
        # Check for coordinate duplicates
        self._check_coordinate_duplicates(result)
        
        return result
    
    def _validate_poi(self, poi: Dict[str, Any], result: ValidationResult, all_ids: Set[str]):
        """Validate a single POI."""
        poi_id = poi.get("id", "unknown")
        
        # Check unique ID
        if poi_id in all_ids:
            result.add_error(poi_id, "poi", "id", "Duplicate ID")
        else:
            all_ids.add(poi_id)
        
        # Check opening_hours format (HH:MM-HH:MM or null)
        opening_hours = poi.get("opening_hours")
        if opening_hours is not None:
            if not self.HOURS_PATTERN.match(opening_hours):
                # Check if it's in opening_hours_note instead (which is acceptable)
                if "opening_hours_note" not in poi:
                    result.add_warning(poi_id, "poi", "opening_hours", 
                                       f"Invalid format: '{opening_hours}'. Expected HH:MM-HH:MM or null")
        
        # Check coordinates
        coords = poi.get("coordinates", {})
        self._check_coordinates(poi_id, "poi", coords, result)
        
        # Check verified sources
        if poi.get("confidence") == "verified":
            if not poi.get("source"):
                result.add_warning(poi_id, "poi", "source", 
                                   "confidence='verified' but source is missing")
    
    def _validate_restaurant(self, rest: Dict[str, Any], result: ValidationResult, all_ids: Set[str]):
        """Validate a single restaurant."""
        rest_id = rest.get("id", "unknown")
        
        # Check unique ID
        if rest_id in all_ids:
            result.add_error(rest_id, "restaurant", "id", "Duplicate ID")
        else:
            all_ids.add(rest_id)
        
        # Check required fields: type, opens_at, closing_hours, coordinates
        # Note: 'type' field is optional in current schema, category is used
        
        # Check opens_at format (HH:MM)
        opens_at = rest.get("opens_at")
        if not opens_at:
            result.add_error(rest_id, "restaurant", "opens_at", "Missing opens_at")
        elif not self.TIME_PATTERN.match(opens_at):
            result.add_error(rest_id, "restaurant", "opens_at", 
                             f"Invalid format: '{opens_at}'. Expected HH:MM")
        
        # Check closing_hours format (HH:MM)
        closing_hours = rest.get("closing_hours")
        if not closing_hours:
            result.add_error(rest_id, "restaurant", "closing_hours", "Missing closing_hours")
        elif not self.TIME_PATTERN.match(closing_hours):
            result.add_error(rest_id, "restaurant", "closing_hours", 
                             f"Invalid format: '{closing_hours}'. Expected HH:MM")
        
        # Check coordinates
        coords = rest.get("coordinates", {})
        if not coords:
            result.add_error(rest_id, "restaurant", "coordinates", "Missing coordinates")
        else:
            self._check_coordinates(rest_id, "restaurant", coords, result)
    
    def _validate_hotel(self, hotel: Dict[str, Any], result: ValidationResult, all_ids: Set[str]):
        """Validate a single hotel."""
        hotel_id = hotel.get("id", "unknown")
        
        # Check unique ID
        if hotel_id in all_ids:
            result.add_error(hotel_id, "hotel", "id", "Duplicate ID")
        else:
            all_ids.add(hotel_id)
        
        # Check coordinates
        coords = hotel.get("coordinates", {})
        if coords:
            self._check_coordinates(hotel_id, "hotel", coords, result)
    
    def _check_coordinates(self, item_id: str, item_type: str, 
                           coords: Dict[str, float], result: ValidationResult):
        """Check coordinates are within Samarkand bounds."""
        lat = coords.get("lat")
        lng = coords.get("lng")
        
        if lat is None or lng is None:
            result.add_warning(item_id, item_type, "coordinates", "Missing lat/lng")
            return
        
        bounds = self.SAMARKAND_BOUNDS
        if not (bounds["lat_min"] <= lat <= bounds["lat_max"]):
            result.add_warning(item_id, item_type, "coordinates.lat", 
                               f"Latitude {lat} outside Samarkand bounds")
        
        if not (bounds["lng_min"] <= lng <= bounds["lng_max"]):
            result.add_warning(item_id, item_type, "coordinates.lng", 
                               f"Longitude {lng} outside Samarkand bounds")
    
    def _check_coordinate_duplicates(self, result: ValidationResult):
        """Check for duplicate coordinates (potential data errors)."""
        coord_map: Dict[Tuple[float, float], List[str]] = {}
        
        # Collect all coordinates
        for poi in self.poi_data.get("poi", []):
            coords = poi.get("coordinates", {})
            if coords.get("lat") and coords.get("lng"):
                key = (round(coords["lat"], 4), round(coords["lng"], 4))
                coord_map.setdefault(key, []).append(f"poi:{poi.get('id')}")
        
        for rest in self.hr_data.get("restaurants", []):
            coords = rest.get("coordinates", {})
            if coords.get("lat") and coords.get("lng"):
                key = (round(coords["lat"], 4), round(coords["lng"], 4))
                coord_map.setdefault(key, []).append(f"restaurant:{rest.get('id')}")
        
        # Report duplicates
        for coord, items in coord_map.items():
            if len(items) > 1:
                result.add_warning(items[0], "system", "coordinates", 
                                   f"Same coordinates as: {', '.join(items[1:])}")


def validate_on_startup() -> ValidationResult:
    """Run validation and return result. Call this at API startup."""
    validator = DataValidator()
    return validator.validate_all()


if __name__ == "__main__":
    # Run as standalone script
    print("🔍 SaFar Data Validator\n")
    result = validate_on_startup()
    print(result.summary())
    
    if not result.is_valid:
        print("\n📋 Full error list:")
        for issue in result.errors:
            print(f"   - {issue.item_type}/{issue.item_id}: {issue.field} - {issue.message}")
