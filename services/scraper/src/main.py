"""
Servicio principal de Scraping
Gestiona la ejecución programada de scrapers y publicación de eventos
"""
import os
import time
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import redis
import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from scrapers.igepn_scraper import IGEPNScraper
from scrapers.inamhi_scraper import InamhiScraper
from scrapers.cnel_scraper import CnelScraper
from scrapers.usgs_scraper import USGSScraper
from scrapers.open_meteo_scraper import OpenMeteoScraper

# Configurar logging estructurado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Configuración desde variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://sacv:password@rabbitmq:5672')

class ScraperService:
    """Servicio de scraping con scheduling y publicación a RabbitMQ"""
    
    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.rabbitmq_conn = None
        self.rabbitmq_channel = None
        self.scheduler = BackgroundScheduler()
        self.scrapers = {
            'sismo': IGEPNScraper,
            'lluvia': InamhiScraper,
            'corte': CnelScraper
        }
        
    def connect_db(self):
        """Conectar a PostgreSQL con retry"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.db_conn = psycopg2.connect(DATABASE_URL)
                logger.info("database_connected", attempt=attempt + 1)
                return
            except Exception as e:
                logger.warning("database_connection_retry", 
                             attempt=attempt + 1, 
                             max_retries=max_retries,
                             error=str(e))
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("database_connection_failed", error=str(e))
                    raise
    
    def connect_redis(self):
        """Conectar a Redis"""
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            self.redis_client.ping()
            logger.info("redis_connected")
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
    
    def connect_rabbitmq(self):
        """Conectar a RabbitMQ con retry"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                params = pika.URLParameters(RABBITMQ_URL)
                self.rabbitmq_conn = pika.BlockingConnection(params)
                self.rabbitmq_channel = self.rabbitmq_conn.channel()
                
                # Declarar queue con durabilidad
                self.rabbitmq_channel.queue_declare(
                    queue='raw_events', 
                    durable=True
                )
                
                logger.info("rabbitmq_connected", attempt=attempt + 1)
                return
            except Exception as e:
                logger.warning("rabbitmq_connection_retry",
                             attempt=attempt + 1,
                             max_retries=max_retries,
                             error=str(e))
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("rabbitmq_connection_failed", error=str(e))
                    raise
    
    def get_active_sources(self):
        """Obtener fuentes activas de la base de datos"""
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT source_id, name, base_url, type, domain, 
                       parser_config, frequency_sec
                FROM sources
                WHERE active = true
                ORDER BY name
            """)
            sources = cursor.fetchall()
            logger.info("sources_loaded", count=len(sources))
            return [dict(source) for source in sources]
        except Exception as e:
            logger.error("get_sources_failed", error=str(e))
            return []
        finally:
            cursor.close()
    
    def save_raw_event(self, event, source_id=None):
        """Guardar evento crudo en la base de datos"""
        import hashlib
        import uuid
        
        cursor = self.db_conn.cursor()
        try:
            # Si el evento no tiene source_id, fetched_at o raw_hash, los generamos
            if 'source_id' not in event and source_id:
                event['source_id'] = source_id
            
            if 'fetched_at' not in event:
                event['fetched_at'] = datetime.utcnow().isoformat()
            
            if 'raw_hash' not in event:
                # Generar hash del payload
                payload_str = json.dumps(event.get('raw_payload', event), sort_keys=True)
                event['raw_hash'] = hashlib.sha256(payload_str.encode()).hexdigest()
            
            # Si el evento es el payload directo (formato nuevo de IGEPNScraper)
            if 'raw_payload' not in event:
                raw_payload = event
                event = {
                    'source_id': source_id,
                    'fetched_at': datetime.utcnow().isoformat(),
                    'raw_payload': raw_payload,
                    'raw_hash': hashlib.sha256(json.dumps(raw_payload, sort_keys=True).encode()).hexdigest()
                }
            
            cursor.execute("""
                INSERT INTO raw_events (source_id, fetched_at, raw_payload, raw_hash)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (raw_hash) DO NOTHING
                RETURNING raw_id
            """, (
                event['source_id'],
                event['fetched_at'],
                json.dumps(event['raw_payload']),
                event['raw_hash']
            ))
            
            result = cursor.fetchone()
            self.db_conn.commit()
            
            if result:
                raw_id = str(result[0])
                logger.info("raw_event_saved", 
                           raw_id=raw_id,
                           hash=event['raw_hash'][:8])
                return raw_id
            else:
                logger.info("raw_event_duplicate", 
                           hash=event['raw_hash'][:8])
                return None
                
        except Exception as e:
            self.db_conn.rollback()
            logger.error("save_raw_event_failed", error=str(e))
            return None
        finally:
            cursor.close()
    
    def publish_to_queue(self, event):
        """Publicar evento a RabbitMQ"""
        try:
            message = json.dumps(event)
            self.rabbitmq_channel.basic_publish(
                exchange='',
                routing_key='raw_events',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json'
                )
            )
            logger.info("event_published_to_queue", 
                       hash=event['raw_hash'][:8])
        except Exception as e:
            logger.error("publish_failed", error=str(e))
            # Intentar reconectar
            try:
                self.connect_rabbitmq()
                self.rabbitmq_channel.basic_publish(
                    exchange='',
                    routing_key='raw_events',
                    body=message,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                logger.info("event_published_after_reconnect")
            except Exception as e2:
                logger.error("publish_retry_failed", error=str(e2))
    
    def scrape_source(self, source_config):
        """Ejecutar scraping de una fuente específica"""
        source_name = source_config['name']
        source_id = str(source_config['source_id'])
        
        logger.info("scraping_job_started", 
                   source=source_name,
                   source_id=source_id)
        
        # Verificar rate limit en Redis
        rate_key = f"rate_limit:{source_id}"
        if self.redis_client.exists(rate_key):
            logger.warning("rate_limited", 
                          source=source_name,
                          ttl=self.redis_client.ttl(rate_key))
            return
        
        # Selección de scraper
        scraper = None
        base = source_config['base_url'].lower()

        if source_config['type'] == 'sismo':

            if 'usgs' in base:
                scraper = USGSScraper()
                logger.info("using_usgs_scraper", source=source_name)

            elif 'igepn' in base:
                scraper = IGEPNScraper()
                logger.info("using_igepn_scraper", source=source_name)

            else:
                logger.error("unknown_seismic_source", source=source_name)
                return

        elif source_config['type'] == 'lluvia':

            if 'open-meteo' in base:
                config = source_config.get('parser_config', {})
                lat = config.get('lat')
                lon = config.get('lon')
                city = config.get('city', 'Ubicación Desconocida')

                if lat and lon:
                    scraper = OpenMeteoScraper(lat, lon, city)
                    logger.info("using_open_meteo_scraper", source=source_name)
                else:
                    logger.error("missing_weather_config", source=source_name)
                    return
            else:
                scraper = InamhiScraper(source_config)
                logger.info("using_inamhi_scraper", source=source_name)

        elif source_config['type'] == 'corte':
            scraper = CnelScraper(source_config)


        if scraper is None:
            logger.error("scraper_not_found", source=source_name)
            return
        
        event = scraper.scrape()
        
        if event:
            # Guardar en base de datos
            raw_id = self.save_raw_event(event, source_id)
            
            if raw_id:
                # Publicar a queue para procesamiento
                event['raw_id'] = raw_id
                self.publish_to_queue(event)
                
                # Setear rate limit (60 segundos por defecto)
                self.redis_client.setex(rate_key, 60, "1")
                
                logger.info("scraping_job_completed",
                           source=source_name,
                           raw_id=raw_id)
        else:
            logger.warning("scraping_job_no_data", source=source_name)
    
    def schedule_sources(self):
        """Programar scrapers según frecuencia configurada"""
        sources = self.get_active_sources()
        
        if not sources:
            logger.warning("no_active_sources_found")
            # Programar verificación cada 5 minutos
            self.scheduler.add_job(
                self.schedule_sources,
                'interval',
                minutes=5,
                id='refresh_sources',
                replace_existing=True
            )
            return
        
        for source in sources:
            source_id = str(source['source_id'])
            frequency = source.get('frequency_sec', 300)
            
            self.scheduler.add_job(
                self.scrape_source,
                'interval',
                seconds=frequency,
                args=[source],
                id=source_id,
                replace_existing=True
            )
            
            logger.info("source_scheduled", 
                       source=source['name'],
                       frequency_sec=frequency)
    
    def run(self):
        logger.info("scraper_service_starting")

        logger.info("connecting_to_services")
        self.connect_db()
        self.connect_redis()
        self.connect_rabbitmq()

        logger.info("scheduling_sources")
        self.schedule_sources()

        logger.info("scheduler_started", 
                   jobs=len(self.scheduler.get_jobs()))

        # Iniciar scheduler en background
        self.scheduler.start()
        
        import threading
        threading.current_thread().name = "MainThread"
        
        logger.info("scheduler_running_forever")

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("scraper_service_stopping")
            if self.rabbitmq_conn:
                self.rabbitmq_conn.close()
            if self.db_conn:
                self.db_conn.close()

if __name__ == "__main__":
    service = ScraperService()
    service.run()
