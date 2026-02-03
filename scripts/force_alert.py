"""
Script de INYECCIÓN DIRECTA DE ALERTA
Se salta el Scraper, el Normalizer y el Verifier.
Habla directamente con el servicio de Notificaciones.
"""
import pika
import json
import uuid
import datetime

# Configuración
RABBITMQ_URL = 'amqp://sacv:rabbitmq_secure_password_2026@localhost:5672/'

def force_telegram_notification():
    print("\n" + "="*60)
    print("🚨 INYECCIÓN DE ALERTA FORZADA")
    print("="*60)
    print("🎯 Objetivo: Comprobar conexión con Telegram inmediatamente.")

    # 1. Creamos un evento que ya parece verificado y confirmado
    confirmed_payload = {
        "event_id": str(uuid.uuid4()),
        "type": "sismo",
        "province_id": 17,  # <--- ID 17 = PICHINCHA (Asegúrate de estar suscrito a Pichincha)
        "severity": "ALTA",
        "title": "🚨 ALERTA DE PRUEBA: Sismo Simulado en Quito",
        "content": "Esto es una prueba del sistema de notificación. Si lees esto, el bot funciona.",
        "latitude": "-0.18",
        "longitude": "-78.46",
        "depth": "5 km",
        "magnitude": "8.5", # Exagerado para que destaque
        "source": "Simulacro Tesis",
        "occurred_at": datetime.datetime.utcnow().isoformat(),
        "status": "CONFIRMADO",
        "score": 100
    }

    try:
        # 2. Conexión directa a la cola de eventos confirmados
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Declaramos la cola que escucha el Notifier
        channel.queue_declare(queue='confirmed_events', durable=True)

        # 3. Publicar
        channel.basic_publish(
            exchange='',
            routing_key='confirmed_events',
            body=json.dumps(confirmed_payload),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
        
        print("\n✅ [ENVIADO] Paquete 'CONFIRMADO' puesto en la cola del Notifier.")
        print("📨 El bot de Telegram debería sonar en 3... 2... 1...")
        print("\n🔎 Si no suena, revisa:")
        print("   1. Que estés suscrito a PICHINCHA en el bot (/suscribir).")
        print("   2. Los logs: docker logs -f sacv_notifier")
        
        connection.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    force_telegram_notification()
