import requests
import structlog
from datetime import datetime

logger = structlog.get_logger()

class OpenMeteoScraper:
    def __init__(self, lat, lon, city_name, demo_mode=True):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.lat = lat
        self.lon = lon
        self.city_name = city_name
        self.demo_mode = demo_mode  # ← Permite activar o desactivar lluvia falsa

    def scrape(self):
        try:
            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "current": "rain,weather_code,temperature_2m",
                "timezone": "auto"
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            current = data.get("current", {})

            # ---------------------------------------------------------
            # MODO DEMO: lluvia falsa para pruebas
            # ---------------------------------------------------------
            if self.demo_mode:
                rain_mm = 25.5
                temp = current.get("temperature_2m", 18.0)
                wmo_code = current.get("weather_code", 0)

                logger.warning(
                    "weather_check_demo",
                    city=self.city_name,
                    rain_override=rain_mm,
                    temp=temp,
                    status="DEMO_MODE_ACTIVE"
                )
            else:
                rain_mm = current.get("rain", 0.0) or 0.0
                temp = current.get("temperature_2m", 0.0)
                wmo_code = current.get("weather_code", 0)

                logger.info("weather_check", city=self.city_name, rain=rain_mm, temp=temp)

            # No hay lluvia → No se genera evento
            if rain_mm <= 0.0:
                return None

            # ---------------------------------------------------------
            # **EVENTO COMPLETO + raw_payload** → CORRIGE KeyError
            # ---------------------------------------------------------
            payload = {
                "raw_payload": {       # ← necesario para el normalizer
                    "provider": "Open-Meteo",
                    "api_response": current
                },

                "date": datetime.utcnow().isoformat(),
                "latitude": str(self.lat),
                "longitude": str(self.lon),
                "rain_mm": f"{rain_mm} mm",
                "temperature": f"{temp} °C",
                "zone_raw": f"{self.city_name}, Ecuador",

                "title": f"🌧️ Lluvia INTENSA detectada en {self.city_name}",
                "content": (
                    f"ALERTA METEOROLÓGICA: Se registran precipitaciones fuertes "
                    f"de {rain_mm} mm. Precaución en zonas bajas."
                ),

                # Fuente siempre funcional
                "source": "Open-Meteo / IGEPN Monitor Clima",
                "url": "https://www.igepn.edu.ec",

                "severity": "ALTA"
            }

            logger.info(
                "rain_event_found",
                city=self.city_name,
                mm=rain_mm,
                severity="ALTA"
            )

            return payload

        except Exception as e:
            logger.error("meteo_scraping_failed", error=str(e))
            return None
