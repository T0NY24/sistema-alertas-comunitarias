"""
Scraper para Instituto Geofísico del Ecuador (IGEPN) - Sismos
URL: https://www.igepn.edu.ec/servicios/ultimo-sismo
"""
import requests
from bs4 import BeautifulSoup
import hashlib
import json
import structlog
from datetime import datetime

logger = structlog.get_logger()

class IGEPNScraper:
    """Scraper para eventos sísmicos del Instituto Geofísico"""
    
    def __init__(self):
        self.url = "https://www.igepn.edu.ec/servicios/ultimo-sismo"

    def scrape(self):
        """Extrae el último sismo de la página del IGEPN"""
        try:
            # 1. Descargar el HTML
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()

            # 2. Parsear con BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscamos el div que contiene la info del último sismo (suele estar destacado)
            # Ojo: La estructura del IGEPN cambia, pero generalmente usan tablas o divs con clases específicas
            # Para este ejemplo, buscamos el primer evento de la lista
            
            # NOTA: Ajusta estos selectores si el IGEPN cambia su diseño
            bloque_sismo = soup.find('div', id='ultimo_sismo_container') 
            
            # Si no hay ID específico, buscamos la primera fila de la tabla de reportes
            if not bloque_sismo:
                # Buscamos la tabla clásica
                tabla = soup.find('table')
                if tabla:
                    rows = tabla.find_all('tr')
                    if len(rows) > 1:
                        # Extraemos datos de la primera fila (el más reciente)
                        cols = rows[1].find_all('td')
                        if len(cols) >= 5:
                            fecha = cols[0].text.strip()
                            lat = cols[1].text.strip()
                            lon = cols[2].text.strip()
                            prof = cols[3].text.strip()
                            mag = cols[4].text.strip()
                            zona = cols[5].text.strip() if len(cols) > 5 else "Ecuador"
                            
                            # Construimos el payload crudo
                            payload = {
                                "date": fecha,
                                "latitude": lat,
                                "longitude": lon,
                                "depth": prof,
                                "magnitude": mag,
                                "zone_raw": zona,
                                "source": "IGEPN",
                                "scraped_at": datetime.utcnow().isoformat()
                            }
                            
                            logger.info("sismo_scraped", 
                                       magnitude=mag, 
                                       zone=zona[:30],
                                       date=fecha)
                            return payload

            logger.warning("structure_change", msg="No se encontró la tabla de sismos")
            return None

        except Exception as e:
            logger.error("scraping_failed", url=self.url, error=str(e))
            return None
