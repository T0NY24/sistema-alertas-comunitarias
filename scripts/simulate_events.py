"""
SACV - Simulador de Alertas Oficial
Script para enviar eventos de prueba a RabbitMQ y verificar el sistema de notificaciones
"""
import pika
import json
import uuid
import sys
import os

# Configuración de RabbitMQ (ajusta según tu .env)
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'sacv'
RABBITMQ_PASSWORD = 'rabbitmq_secure_password_2026'


def enviar_alerta(event_type, zone, title, description, severity="Media"):
    """
    Envía un evento de prueba a la cola confirmed_events de RabbitMQ
    """
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
        
        # Declarar la cola (por si no existe)
        channel.queue_declare(queue='confirmed_events', durable=True)
        
        # Declarar la cola (por si no existe)
        channel.queue_declare(queue='confirmed_events', durable=True)
        
        # Crear payload del evento
        payload = {
            "event_id": str(uuid.uuid4()),
            "type": event_type,
            "zone": zone,
            "title": title,
            "description": description,
            "severity": severity,
            "score": 85,
            "evidence_url": "https://www.igepn.edu.ec/",
            "occurred_at": "2026-01-30T10:00:00"
        }
        
        # Publicar mensaje
        channel.basic_publish(
            exchange='',
            routing_key='confirmed_events',
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
            )
        )
        
        print(f"\n✅ [EXITO] Evento '{event_type}' enviado a la zona '{zone}'")
        print(f"   📋 Título: {title}")
        print(f"   📝 Descripción: {description}")
        print(f"   🎯 Severidad: {severity}")
        print(f"   🆔 Event ID: {payload['event_id']}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"\n❌ [ERROR] No se pudo conectar a RabbitMQ: {e}")
        print(f"   💡 Verifica que Docker esté corriendo: docker-compose ps")
        return False


def mostrar_menu():
    """Muestra el menú interactivo"""
    print("\n" + "="*50)
    print("🚀 SACV - SIMULADOR DE ALERTAS OFICIAL")
    print("="*50)
    print("\n📍 EVENTOS PREDEFINIDOS:")
    print("1. 🌍 Sismo en PICHINCHA (Magnitud 4.8)")
    print("2. 🌧️  Lluvia en GUAYAS (Alerta Meteorológica)")
    print("3. ⚡ Corte de Energía en LOJA (Mantenimiento)")
    print("4. 🌍 Sismo en AZUAY (Magnitud 5.2)")
    print("5. 🌧️  Lluvia en MANABI (Lluvias intensas)")
    print("6. ⚡ Corte en TUNGURAHUA (Emergencia)")
    print("\n🔧 OPCIONES AVANZADAS:")
    print("7. ✏️  Evento Personalizado")
    print("8. 🔄 Enviar múltiples eventos de prueba")
    print("\n0. ❌ Salir")
    print("="*50)


def evento_personalizado():
    """Permite crear un evento personalizado"""
    print("\n📝 CREAR EVENTO PERSONALIZADO")
    print("-" * 40)
    
    print("\nTipos disponibles: sismo, lluvia, corte")
    event_type = input("👉 Tipo de evento: ").lower().strip()
    
    print("\nProvincias disponibles:")
    print("AZUAY, BOLIVAR, CAÑAR, CARCHI, CHIMBORAZO, COTOPAXI")
    print("EL ORO, ESMERALDAS, GUAYAS, IMBABURA, LOJA, LOS RIOS")
    print("MANABI, PICHINCHA, SANTA ELENA, TUNGURAHUA")
    zone = input("\n👉 Zona (Provincia en MAYÚSCULAS): ").upper().strip()
    
    title = input("👉 Título del evento: ").strip()
    description = input("👉 Descripción: ").strip()
    
    print("\nSeveridad: Alta, Media, Baja")
    severity = input("👉 Severidad (default: Media): ").strip() or "Media"
    
    return enviar_alerta(event_type, zone, title, description, severity)


def enviar_multiples_eventos():
    """Envía varios eventos de prueba para diferentes provincias"""
    print("\n🔄 ENVIANDO EVENTOS DE PRUEBA MÚLTIPLES...")
    print("-" * 40)
    
    eventos = [
        ("sismo", "PICHINCHA", "Sismo detectado en Quito", "Magnitud 4.5, epicentro norte de Quito", "Media"),
        ("lluvia", "GUAYAS", "Alerta meteorológica", "Lluvias intensas en Guayaquil y alrededores", "Alta"),
        ("corte", "AZUAY", "Corte programado CENTROSUR", "Mantenimiento en sector El Ejido", "Baja"),
        ("sismo", "MANABI", "Réplica sísmica", "Magnitud 3.8 en Portoviejo", "Baja"),
    ]
    
    exitosos = 0
    for event_type, zone, title, desc, severity in eventos:
        if enviar_alerta(event_type, zone, title, desc, severity):
            exitosos += 1
    
    print(f"\n✅ Enviados {exitosos}/{len(eventos)} eventos correctamente")


def main():
    """Función principal"""
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\n👉 Selecciona una opción: ").strip()
            
            if opcion == "0":
                print("\n👋 ¡Hasta luego!")
                sys.exit(0)
            
            elif opcion == "1":
                enviar_alerta("sismo", "PICHINCHA", "SISMO DETECTADO", 
                            "Magnitud 4.8 en Quito, epicentro norte", "Media")
            
            elif opcion == "2":
                enviar_alerta("lluvia", "GUAYAS", "ALERTA METEOROLÓGICA", 
                            "Lluvias intensas en Guayaquil y zonas aledañas", "Alta")
            
            elif opcion == "3":
                enviar_alerta("corte", "LOJA", "MANTENIMIENTO CNEL", 
                            "Corte programado sector centro de Loja", "Baja")
            
            elif opcion == "4":
                enviar_alerta("sismo", "AZUAY", "SISMO REGISTRADO", 
                            "Magnitud 5.2 en Cuenca, sentido en toda la provincia", "Alta")
            
            elif opcion == "5":
                enviar_alerta("lluvia", "MANABI", "ALERTA AMARILLA", 
                            "Lluvias intensas en Portoviejo y Manta", "Media")
            
            elif opcion == "6":
                enviar_alerta("corte", "TUNGURAHUA", "EMERGENCIA ELÉCTRICA", 
                            "Corte no programado en Ambato por falla técnica", "Alta")
            
            elif opcion == "7":
                evento_personalizado()
            
            elif opcion == "8":
                enviar_multiples_eventos()
            
            else:
                print("\n⚠️  Opción no válida. Intenta de nuevo.")
            
            input("\n⏸️  Presiona ENTER para continuar...")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            input("\n⏸️  Presiona ENTER para continuar...")


if __name__ == "__main__":
    print("\n🔍 Verificando configuración...")
    print(f"   Host: {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    print(f"   Usuario: {RABBITMQ_USER}")
    
    main()
