"""
SACV - Simulador de Alertas Oficial (Versión IDs Numéricos - 24 Provincias)
Script para enviar eventos de prueba a RabbitMQ manteniendo la estructura original.
"""
import pika
import json
import uuid
import sys
import os
import time
import random

# --- CONFIGURACIÓN DE RABBITMQ ---
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'sacv'
RABBITMQ_PASSWORD = 'rabbitmq_secure_password_2026'

# Mapeo oficial de Provincias e IDs
PROVINCIAS_IDS = {
    "AZUAY": 1, "BOLIVAR": 2, "CAÑAR": 3, "CARCHI": 4, "COTOPAXI": 5,
    "CHIMBORAZO": 6, "EL ORO": 7, "ESMERALDAS": 8, "GUAYAS": 9, "IMBABURA": 10,
    "LOJA": 11, "LOS RIOS": 12, "MANABI": 13, "MORONA SANTIAGO": 14, "NAPO": 15,
    "PASTAZA": 16, "PICHINCHA": 17, "TUNGURAHUA": 18, "ZAMORA CHINCHIPE": 19,
    "GALAPAGOS": 20, "SUCUMBIOS": 21, "ORELLANA": 22, "STO. DOMINGO": 23, "SANTA ELENA": 24
}

def enviar_alerta(event_type, province_name, title, description, severity="Media"):
    """
    Envía un evento de prueba usando el ID Numérico (province_id).
    """
    province_id = PROVINCIAS_IDS.get(province_name.upper())
    
    if not province_id:
        print(f"\n❌ [ERROR] La provincia '{province_name}' no es válida.")
        return False

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue='confirmed_events', durable=True)
        
        # Payload Estándar (El que funcionaba originalmente)
        payload = {
            "event_id": str(uuid.uuid4()),
            "type": event_type,
            "province_id": province_id,      # Enviamos el ID numérico (1-24)
            "province_name": province_name.upper(), 
            "title": title,
            "description": description,
            "severity": severity,
            "score": random.randint(70, 99),
            "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        channel.basic_publish(
            exchange='',
            routing_key='confirmed_events',
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        print(f"✅ [ENVIADO] {province_name:<15} (ID: {province_id:02d}) -> {event_type.upper()}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"\n❌ [ERROR] No se pudo conectar a RabbitMQ: {e}")
        return False

def simular_masivo_24():
    """Recorre las 24 provincias y envía un evento aleatorio a cada una."""
    print("\n" + "!"*60)
    print("🇪🇨 INICIANDO SIMULACIÓN NACIONAL (24 PROVINCIAS) 🇪🇨")
    print("!"*60 + "\n")
    
    tipos = ["sismo", "lluvia", "corte", "incendio", "deslizamiento"]
    severidades = ["Alta", "Media", "Baja"]
    
    count = 0
    for provincia in PROVINCIAS_IDS:
        # Variamos los datos para que no parezcan repetidos
        tipo_evento = random.choice(tipos)
        severidad = random.choice(severidades)
        
        enviar_alerta(
            event_type=tipo_evento,
            province_name=provincia,
            title=f"ALERTA EN {provincia}",
            description=f"Evento de prueba masiva para validación de ID {PROVINCIAS_IDS[provincia]}",
            severity=severidad
        )
        count += 1
        time.sleep(0.1) # Pausa estética
        
    print(f"\n🎉 Simulacion finalizada. Se enviaron {count} eventos.")

def mostrar_menu():
    print("\n" + "="*50)
    print("🚀 SACV - SIMULADOR DE ALERTAS (ORIGINAL)")
    print("="*50)
    print("\n📍 PRUEBAS RÁPIDAS:")
    print("1. 🌍 Sismo en PICHINCHA (ID: 17)")
    print("2. 🌧️  Lluvia en GUAYAS (ID: 9)")
    print("3. ⚡ Corte en LOJA (ID: 11)")
    print("4. 🌍 Sismo en MANABI (ID: 13)")
    print("5. ⚡ Corte en AZUAY (ID: 1)")
    print("\n🔥 PRUEBA DE CARGA:")
    print("6. 🇪🇨 Simulación Masiva (Las 24 Provincias)")
    print("\n🔧 OTRAS OPCIONES:")
    print("7. ✏️  Evento Personalizado (Manual)")
    print("0. ❌ Salir")
    print("="*50)

def evento_personalizado():
    print("\n📝 CREAR EVENTO PERSONALIZADO")
    event_type = input("👉 Tipo (sismo/lluvia/corte): ").lower().strip()
    zone = input("👉 Provincia (MAYÚSCULAS): ").upper().strip()
    title = input("👉 Título: ").strip()
    description = input("👉 Descripción: ").strip()
    severity = input("👉 Severidad (Alta/Media/Baja): ").strip() or "Media"
    return enviar_alerta(event_type, zone, title, description, severity)

def main():
    while True:
        mostrar_menu()
        opcion = input("\n👉 Selecciona una opción: ").strip()
        
        if opcion == "0":
            break
        elif opcion == "1":
            enviar_alerta("sismo", "PICHINCHA", "ALERTA DE SISMO", "Sismo de 4.8 detectado en Quito", "Alta")
        elif opcion == "2":
            enviar_alerta("lluvia", "GUAYAS", "TORMENTA ELÉCTRICA", "Lluvias fuertes en Guayaquil", "Media")
        elif opcion == "3":
            enviar_alerta("corte", "LOJA", "CORTE PROGRAMADO", "Mantenimiento en el centro de Loja", "Baja")
        elif opcion == "4":
            enviar_alerta("sismo", "MANABI", "SISMO DETECTADO", "Sismo de 5.1 cerca de Manta", "Alta")
        elif opcion == "5":
            enviar_alerta("corte", "AZUAY", "FALLA ELÉCTRICA", "Corte imprevisto en Cuenca", "Media")
        elif opcion == "6":
            simular_masivo_24()
        elif opcion == "7":
            evento_personalizado()
        
        input("\n⏸️  Presiona ENTER para continuar...")

if __name__ == "__main__":
    main()