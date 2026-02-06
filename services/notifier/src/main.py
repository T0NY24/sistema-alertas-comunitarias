import os
import json
import time
import uuid
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import structlog
from telegram import Bot
from telegram.request import HTTPXRequest
from email_client import enviar_correo_alerta

# Configurar logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Configuración
DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://sacv:rabbitmq_secure_password_2026@localhost:5672')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

class NotifierService:
    def __init__(self):
        self.db_conn = None
        self.rabbitmq_conn = None
        self.channel = None
        self.request = HTTPXRequest(connection_pool_size=20)
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN, request=self.request)
        
    def connect_db(self):
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            logger.info("database_connected")
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            raise
    
    def connect_rabbitmq(self):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            self.rabbitmq_conn = pika.BlockingConnection(params)
            self.channel = self.rabbitmq_conn.channel()
            self.channel.queue_declare(queue='confirmed_events', durable=True)
            logger.info("rabbitmq_connected")
        except Exception as e:
            logger.error("rabbitmq_connection_failed", error=str(e))
            raise

    def format_message(self, event):
        """Da formato bonito al mensaje de Telegram"""
        try:
            # Iconos según severidad
            icons = {
                "ALTA": "🚨🔴",
                "MEDIA": "⚠️🟠",
                "BAJA": "ℹ️🟢"
            }
            severity = event.get('severity', 'MEDIA')
            icon = icons.get(severity, "⚠️")
            
            # Extraemos datos asegurando que no sean None
            title = event.get('title', 'Alerta de Evento')
            # AQUÍ ESTABA EL ERROR: Usar 'content' en vez de 'detail'
            content = event.get('content') or event.get('detail') or event.get('description') or "Sin detalles disponibles."
            province = event.get('zone_raw') or event.get('province_name') or "Zona no especificada"
            mag = event.get('magnitude', 'N/A')
            
            # Construimos el mensaje final
            message = (
                f"{icon} *{title}*\n\n"
                f"📍 *Ubicación:* {province}\n"
                f"📉 *Magnitud:* {mag}\n"
                f"📝 *Detalle:* {content}\n\n"
                f"🕒 *Hora:* {event.get('occurred_at', 'N/A')}\n"
                f"🔗 _Fuente: Sistema de Alertas Comunitarias_"
            )
            return message
            
        except Exception as e:
            logger.error("format_error", error=str(e))
            return "🚨 Alerta recibida (Error de formato)"

    async def send_telegram_msg(self, chat_id, event):
        """Envío con formato profesional"""
        mensaje = self.format_message(event)
        async with self.bot:
            await self.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')
            return True

    def get_subscriptions(self, event):
        """
        Busca suscriptores de la provincia específica 
        Y suscriptores nacionales (ID 0) si la severidad es alta.
        """
        if not self.db_conn: return []
        
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        
        province_id = event.get('province_id')
        severity = event.get('severity', 'Baja').capitalize() # Asegura 'Alta', 'Media', 'Baja'
        
        try:
            # 🧠 LÓGICA DE SQL MEJORADA
            # 1. Trae a los de la provincia exacta.
            # 2. O trae a los de ID 0 (Nacional) PERO SOLO SI es Alta o Media.
            query = """
                SELECT s.sub_id, s.channel_id
                FROM subscriptions s
                WHERE s.active = true
                  AND (
                      s.province_id = %s
                      OR 
                      (s.province_id = 0 AND %s IN ('Alta', 'Media'))
                  )
            """
            
            cursor.execute(query, (province_id, severity))
            return cursor.fetchall()

        except Exception as e:
            self.db_conn.rollback()
            logger.error("get_subscriptions_failed", error=str(e))
            return []
        finally:
            cursor.close()

    def save_notification(self, sub_id, event_id, chat_id, status, error=None):
        """Intento de guardado con manejo de error de Foreign Key"""
        cursor = self.db_conn.cursor()
        try:
            notif_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notifications (notif_id, event_id, sub_id, channel, to_address, sent_at, status, error_message)
                VALUES (%s, %s, %s, 'telegram', %s, CURRENT_TIMESTAMP, %s, %s)
            """, (notif_id, event_id, sub_id, str(chat_id), status, error))
            self.db_conn.commit()
        except psycopg2.errors.ForeignKeyViolation:
            self.db_conn.rollback()
            logger.warning("save_notification_skipped_fk", reason="event_id_not_in_db_yet")
        except Exception as e:
            self.db_conn.rollback()
            logger.error("save_notification_failed", error=str(e))
        finally:
            cursor.close()

    async def process_event(self, event):
        event_id = event.get('event_id')
        subs = self.get_subscriptions(event)
        
        if not subs:
            logger.info("no_subscriptions_found", province_id=event.get('province_id'))
            return

        for s in subs:
            try:
                await self.send_telegram_msg(s['channel_id'], event)
                self.save_notification(s['sub_id'], event_id, s['channel_id'], 'sent')
                logger.info("notification_sent", chat_id=s['channel_id'])
            except Exception as e:
                self.save_notification(s['sub_id'], event_id, s['channel_id'], 'failed', str(e))
                logger.error("notification_failed", chat_id=s['channel_id'], error=str(e))

    def callback(self, ch, method, properties, body):
        event = json.loads(body)
        logger.info("processing_event", event_id=event.get('event_id'))

        # --- 2. NUEVA LÓGICA DE GMAIL ---
        try:
            severity = event.get('severity', 'Baja').capitalize()
            if severity in ['Alta', 'Media']:
                logger.info("high_severity_email_alert", severity=severity)
                enviar_correo_alerta(event)
            else:
                logger.info("low_severity_skip_email", severity=severity)
        except Exception as e:
            logger.error("email_processing_error", error=str(e))
        
        # --- LÓGICA DE TELEGRAM EXISTENTE ---
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_event(event))
        finally:
            loop.close()
            
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        self.connect_db()
        self.connect_rabbitmq()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='confirmed_events', on_message_callback=self.callback)
        logger.info("waiting_for_events")
        self.channel.start_consuming()

if __name__ == "__main__":
    NotifierService().run()