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
        # Aumentamos el pool para evitar el 'Pool timeout'
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

    async def send_telegram_msg(self, chat_id, event):
        """Envío asíncrono robusto"""
        mensaje = (
            f"🚨 *ALERTA: {event.get('type', 'EVENTO').upper()}*\n\n"
            f"📍 *Zona:* {event.get('zone')}\n"
            f"📝 *Detalle:* {event.get('description')}\n"
            f"📅 *Fecha:* {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        # Usamos 'async with bot' para asegurar que el loop no se cierre prematuramente
        async with self.bot:
            await self.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')
            return True

    def get_subscriptions(self, event):
        """Consulta alineada a tus tablas: sub_id, channel_id, email"""
        cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT s.sub_id, s.user_id, s.channel_id, u.email
                FROM subscriptions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.active = true
                  AND s.zone = %s
                  AND (s.type = %s OR s.type IS NULL)
            """, (event.get('zone'), event.get('type')))
            return cursor.fetchall()
        except Exception as e:
            self.db_conn.rollback()
            logger.error("get_subscriptions_failed", error=str(e))
            return []
        finally:
            cursor.close()

    def save_notification(self, sub_id, event_id, chat_id, status, error=None):
        """Insert corregido con to_address"""
        cursor = self.db_conn.cursor()
        try:
            notif_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notifications (notif_id, event_id, sub_id, channel, to_address, status, error_message)
                VALUES (%s, %s, %s, 'telegram', %s, %s, %s)
            """, (notif_id, event_id, sub_id, str(chat_id), status, error))
            self.db_conn.commit()
        except Exception as e:
            self.db_conn.rollback()
            logger.error("save_notification_failed", error=str(e))
        finally:
            cursor.close()

    async def process_event(self, event):
        event_id = event.get('event_id')
        subs = self.get_subscriptions(event)
        
        if not subs:
            logger.info("no_subscriptions_found", zone=event.get('zone'))
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
        
        # Ejecución en un loop nuevo por cada mensaje para evitar 'loop is closed'
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