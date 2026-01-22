"""
Weather Service - Fetches weather forecast and adapts travel plans accordingly.
Uses Open-Meteo free API (no API key required).
"""

import httpx
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class DayForecast:
    """Weather forecast for a single day."""
    date: date
    temp_max: float
    temp_min: float
    precipitation_mm: float
    weather_code: int
    weather_description: str
    is_good_for_outdoor: bool
    recommendation: str


# WMO Weather interpretation codes
WEATHER_CODES = {
    0: ("☀️ Ясно", True),
    1: ("🌤️ Преимущественно ясно", True),
    2: ("⛅ Переменная облачность", True),
    3: ("☁️ Пасмурно", True),
    45: ("🌫️ Туман", False),
    48: ("🌫️ Изморозь", False),
    51: ("🌧️ Лёгкая морось", False),
    53: ("🌧️ Морось", False),
    55: ("🌧️ Сильная морось", False),
    61: ("🌧️ Небольшой дождь", False),
    63: ("🌧️ Дождь", False),
    65: ("🌧️ Сильный дождь", False),
    71: ("🌨️ Небольшой снег", False),
    73: ("🌨️ Снег", False),
    75: ("🌨️ Сильный снег", False),
    80: ("🌧️ Ливень", False),
    81: ("🌧️ Сильный ливень", False),
    82: ("⛈️ Очень сильный ливень", False),
    95: ("⛈️ Гроза", False),
    96: ("⛈️ Гроза с градом", False),
    99: ("⛈️ Сильная гроза с градом", False),
}


class WeatherService:
    """
    Weather service for Samarkand using Open-Meteo API.
    Provides forecast and travel recommendations.
    """
    
    API_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Samarkand coordinates
    DEFAULT_LAT = 39.6542
    DEFAULT_LNG = 66.9597
    
    def __init__(self, lat: float = None, lng: float = None):
        self.lat = lat or self.DEFAULT_LAT
        self.lng = lng or self.DEFAULT_LNG
    
    async def get_forecast(self, days: int = 7) -> List[DayForecast]:
        """
        Get weather forecast for the specified number of days.
        
        Args:
            days: Number of days to forecast (1-16)
        
        Returns:
            List of DayForecast objects
        """
        
        params = {
            "latitude": self.lat,
            "longitude": self.lng,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min", 
                "precipitation_sum",
                "weathercode"
            ],
            "timezone": "Asia/Tashkent",
            "forecast_days": min(days, 16)
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.API_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
            return self._parse_forecast(data)
        except Exception as e:
            # Return mock forecast on error
            return self._mock_forecast(days)
    
    def get_forecast_sync(self, days: int = 7) -> List[DayForecast]:
        """Synchronous version of get_forecast."""
        
        params = {
            "latitude": self.lat,
            "longitude": self.lng,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "Asia/Tashkent",
            "forecast_days": min(days, 16)
        }
        
        try:
            with httpx.Client() as client:
                response = client.get(self.API_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
            return self._parse_forecast(data)
        except Exception as e:
            return self._mock_forecast(days)
    
    def _parse_forecast(self, data: Dict) -> List[DayForecast]:
        """Parse API response into DayForecast objects."""
        
        forecasts = []
        daily = data.get("daily", {})
        
        dates = daily.get("time", [])
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        codes = daily.get("weathercode", [])
        
        for i in range(len(dates)):
            weather_code = codes[i] if i < len(codes) else 0
            description, is_good = WEATHER_CODES.get(weather_code, ("❓ Неизвестно", True))
            
            # Generate recommendation
            temp_max = temps_max[i] if i < len(temps_max) else 20
            precipitation = precip[i] if i < len(precip) else 0
            recommendation = self._get_recommendation(weather_code, temp_max, precipitation)
            
            forecast = DayForecast(
                date=datetime.strptime(dates[i], "%Y-%m-%d").date(),
                temp_max=temp_max,
                temp_min=temps_min[i] if i < len(temps_min) else 10,
                precipitation_mm=precipitation,
                weather_code=weather_code,
                weather_description=description,
                is_good_for_outdoor=is_good and precipitation < 5,
                recommendation=recommendation
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def _get_recommendation(self, code: int, temp: float, precip: float) -> str:
        """Generate travel recommendation based on weather."""
        
        recommendations = []
        
        # Temperature-based
        if temp > 35:
            recommendations.append("🥵 Жарко! Посещайте outdoor места утром или вечером")
        elif temp > 30:
            recommendations.append("☀️ Тепло. Берите воду и головной убор")
        elif temp < 5:
            recommendations.append("🧥 Холодно. Одевайтесь тепло")
        elif temp < 15:
            recommendations.append("🧣 Прохладно. Возьмите куртку")
        
        # Precipitation-based
        if precip > 10:
            recommendations.append("☂️ Сильный дождь. Рекомендуем музеи и крытые места")
        elif precip > 2:
            recommendations.append("🌂 Возможен дождь. Возьмите зонт")
        
        # Weather code specific
        if code >= 95:
            recommendations.append("⛈️ Гроза! Избегайте открытых пространств")
        elif code in [45, 48]:
            recommendations.append("🌫️ Туман. Будьте осторожны на дорогах")
        
        if not recommendations:
            recommendations.append("👍 Отличная погода для прогулок!")
        
        return " | ".join(recommendations)
    
    def _mock_forecast(self, days: int) -> List[DayForecast]:
        """Generate mock forecast when API is unavailable."""
        
        forecasts = []
        base_date = date.today()
        
        # Typical January weather in Samarkand
        mock_data = [
            (5, -2, 0, 1),   # Day 1
            (7, 0, 0, 0),    # Day 2
            (4, -3, 2, 61),  # Day 3 - rain
            (6, -1, 0, 2),   # Day 4
            (8, 1, 0, 1),    # Day 5
            (3, -4, 5, 71),  # Day 6 - snow
            (5, -2, 0, 3),   # Day 7
        ]
        
        for i in range(min(days, len(mock_data))):
            temp_max, temp_min, precip, code = mock_data[i]
            description, is_good = WEATHER_CODES.get(code, ("❓", True))
            
            forecast = DayForecast(
                date=base_date + timedelta(days=i),
                temp_max=temp_max,
                temp_min=temp_min,
                precipitation_mm=precip,
                weather_code=code,
                weather_description=description,
                is_good_for_outdoor=is_good,
                recommendation=self._get_recommendation(code, temp_max, precip)
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def should_reschedule_outdoor(self, weather_code: int, precipitation: float) -> bool:
        """Check if outdoor activities should be rescheduled."""
        
        bad_codes = [51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99]
        return weather_code in bad_codes or precipitation > 5
    
    def get_best_days(self, forecasts: List[DayForecast], count: int = 3) -> List[DayForecast]:
        """Get the best days for outdoor activities."""
        
        # Sort by outdoor suitability and temperature
        sorted_forecasts = sorted(
            forecasts,
            key=lambda f: (f.is_good_for_outdoor, -abs(f.temp_max - 22)),  # Optimal ~22°C
            reverse=True
        )
        return sorted_forecasts[:count]


# Quick test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        weather = WeatherService()
        forecasts = await weather.get_forecast(7)
        
        print("🌤️ Прогноз погоды для Самарканда:\n")
        for f in forecasts:
            print(f"{f.date.strftime('%a %d.%m')}: {f.weather_description}")
            print(f"   🌡️ {f.temp_min:.0f}°C ... {f.temp_max:.0f}°C")
            print(f"   💧 Осадки: {f.precipitation_mm:.1f} мм")
            print(f"   💡 {f.recommendation}")
            print()
        
        # Best days
        best = weather.get_best_days(forecasts, 2)
        print("\n🌟 Лучшие дни для прогулок:")
        for f in best:
            print(f"   • {f.date.strftime('%A %d.%m')} - {f.weather_description}")
    
    asyncio.run(test())
