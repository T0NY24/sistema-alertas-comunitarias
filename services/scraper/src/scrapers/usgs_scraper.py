"""
Scraper para USGS Earthquake API - Sismos de Ecuador
API: https://earthquake.usgs.gov/fdsnws/event/1/
"""
import requests
import json
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

class USGSScraper:
    """Scraper para eventos sísmicos del USGS filtrados por Ecuador"""
    
    def __init__(self):
        # API oficial del Servicio Geológico de EE.UU.
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    def scrape(self):
        """Consulta la API del USGS para sismos en Ecuador"""
        try:
            # Calculamos "Ayer" para traer datos de las últimas 24h
            ayer = datetime.utcnow() - timedelta(days=1)
            
            # Parámetros para filtrar SOLO Ecuador y sismos relevantes
            params = {
                "format": "geojson",
                "starttime": ayer.strftime("%Y-%m-%d"), # Últimas 24 horas
                "minlatitude": -6.0,   # Sur de Ecuador
                "maxlatitude": 2.0,    # Norte de Ecuador
                "minlongitude": -82.0, # Oeste (Costa/Galápagos)
                "maxlongitude": -75.0, # Este (Amazonía)
                "minmagnitude": 2.0,   # Sismos perceptibles (bajado de 4.0)
                "limit": 1,            # Solo el más reciente
                "orderby": "time"
            }

            logger.info("usgs_api_request", params=params)
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar si hay eventos
            if not data.get('features'):
                logger.info("usgs_no_events_found", 
                           message="No hay sismos >2.0 en Ecuador en las últimas 24h")
                return None

            # Extraer el sismo más reciente
            event = data['features'][0]
            props = event['properties']
            coords = event['geometry']['coordinates'] # [long, lat, depth]

            # Convertir timestamp (ms) a fecha legible
            timestamp = props['time'] / 1000
            fecha_hora = datetime.utcfromtimestamp(timestamp).isoformat()

            # Construir payload compatible con nuestro sistema
            payload = {
                "date": fecha_hora,
                "latitude": str(coords[1]),
                "longitude": str(coords[0]),
                "depth": f"{coords[2]} km",
                "magnitude": str(props['mag']),
                "zone_raw": props['place'], # Ej: "24km SSE of Muisne, Ecuador"
                "source": "USGS API",
                "url": props['url'],
                "scraped_at": datetime.utcnow().isoformat()
            }

            logger.info("usgs_event_found", 
                       place=props['place'], 
                       magnitude=props['mag'],
                       depth=coords[2])
            return payload

        except requests.RequestException as e:
            logger.error("usgs_api_request_failed", 
                        error=str(e),
                        error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("usgs_scraping_failed", 
                        error=str(e),
                        error_type=type(e).__name__)
            return None
