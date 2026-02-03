"""
Script de FUERZA BRUTA para Alerta de Lluvia
Se salta Scraper, Normalizer y Verifier.
Va directo a tu celular.
"""
import pika
import json
import uuid
import datetime

# Configuración
RABBITMQ_URL = 'amqp://sacv:rabbitmq_secure_password_2026@localhost:5672/'

def force_rain_notification():
    print("\n" + "="*60)
    print("🌧️ INYECCIÓN DE ALERTA DE LLUVIA (Loja)")
    print("="*60)

    # 1. Payload simulando una alerta ya verificada
    confirmed_payload = {
        "event_id": str(uuid.uuid4()),
        "type": "clima",            # Tipo Clima
        "province_id": 11,          # <--- ID 11 = LOJA (Asegúrate de estar suscrito a Loja)
        "severity": "ALTA",
        "title": "🌧️ Alerta: Lluvia Torrencial en Loja",
        "content": "Se registran 25.5mm de precipitación en el centro de la ciudad. Riesgo de acumulación de agua.",
        "zone_raw": "Loja, Ecuador",
        "latitude": "-3.99",
        "longitude": "-79.20",
        "rain_mm": "25.5 mm",
        "temp": "18 °C",
        "source": "Simulacro Tesis",
        "occurred_at": datetime.datetime.utcnow().isoformat(),
        "status": "CONFIRMADO",
        "score": 100
    }

    try:
        # 2. Conexión directa a la cola de notificaciones
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
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
        
        print("\n✅ [ENVIADO] Alerta de Lluvia inyectada.")
        print("📨 Revisa tu Telegram. Deberías ver iconos de lluvia/nubes.")
        print("\n⚠️ IMPORTANTE: Si no llega, es porque no estás suscrito a LOJA (ID 11).")
        print("   Ve al bot -> /suscribir -> LOJA")
        
        connection.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    force_rain_notification()
