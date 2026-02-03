"""
Test de integración End-to-End - VERSIÓN "GOLDEN TICKET"
Diseñado para obtener Score > 70 y forzar la notificación.
"""
import pika
import json
import datetime

# Configuración
RABBITMQ_URL = 'amqp://sacv:rabbitmq_secure_password_2026@localhost:5672/'

# UUID REAL (El que ya usaste y funciona)
REAL_USGS_SOURCE_ID = "cdcdfa92-0525-45f8-87ce-ff4df020031c"

def inject_golden_event():
    print("\n" + "="*60)
    print("🧪 TEST END-TO-END: GOLDEN TICKET")
    print("="*60)
    
    # TRUCO 1: Usamos el dominio del IGEPN en la URL para ganar 40 puntos de confianza
    # TRUCO 2: Ponemos 'Quito' explícitamente en el título para el Normalizer
    fake_payload = {
        "date": datetime.datetime.utcnow().isoformat(),
        "latitude": "-0.1807",
        "longitude": "-78.4678",
        "depth": "10 km",
        "magnitude": "6.5",  
        "title": "Sismo Mag 6.5 detectado en QUITO, PICHINCHA", # <--- Clave para la Zona
        "content": "Sismo fuerte sentido en el norte de la capital.",
        "zone_raw": "Quito, Ecuador",
        "source": "USGS API",
        # Usamos una URL que el Verifier ame (dominio .edu.ec)
        "url": "https://www.igepn.edu.ec/servicios/ultimo-sismo/informe-confirmado",
        "scraped_at": datetime.datetime.utcnow().isoformat()
    }

    message = {
        "source_id": REAL_USGS_SOURCE_ID,
        "raw_payload": fake_payload,
        "fetched_at": datetime.datetime.utcnow().isoformat()
    }

    try:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue='raw_events', durable=True)

        channel.basic_publish(
            exchange='',
            routing_key='raw_events',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        print("\n✅ [EXITO] Evento 'Perfecto' inyectado.")
        print("📊 Puntos esperados:")
        print("   +40 (Dominio IGEPN)")
        print("   +15 (URL válida)")
        print("   +15 (Reciente)")
        print("   +10 (Campos completos)")
        print("   ----------------------")
        print("   = 80 Puntos (>70 CONFIRMADO)")
        
        connection.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inject_golden_event()