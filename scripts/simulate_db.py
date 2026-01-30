"""
SACV - Simulador de Eventos vía Base de Datos
Inserta eventos directamente en la tabla events de PostgreSQL
"""
import psycopg2
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()


def simular_evento_db(tipo, zona, titulo, descripcion, severidad="Media"):
    """
    Inserta un evento directamente en la base de datos
    """
    try:
        # Conexión usando credenciales del .env
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host='localhost',  # Desde fuera de Docker usamos localhost
            port='5432'
        )
        cursor = conn.cursor()

        event_id = str(uuid.uuid4())
        
        # Insertar directamente en la tabla de eventos
        query = """
        INSERT INTO events (event_id, type, zone, title, description, severity, status, score, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            event_id, 
            tipo, 
            zona.upper(), 
            titulo, 
            descripcion,
            severidad,
            'confirmed', 
            85,  # Score de confianza
            datetime.now()
        ))

        conn.commit()
        
        print(f"\n✅ [ÉXITO] Evento insertado en la base de datos")
        print(f"   📋 Título: {titulo}")
        print(f"   📍 Zona: {zona.upper()}")
        print(f"   🎯 Tipo: {tipo}")
        print(f"   🆔 Event ID: {event_id}")
        print(f"\n💡 Verifica en DBeaver la tabla 'events' para ver el registro")
        print(f"💡 Si estás suscrito a {zona.upper()}, deberías recibir una notificación en Telegram")

    except Exception as e:
        print(f"\n❌ [ERROR] No se pudo conectar o insertar en la base de datos: {e}")
        print(f"   💡 Verifica que Docker esté corriendo: docker-compose ps")
        print(f"   💡 Verifica las credenciales en el archivo .env")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()


def mostrar_menu():
    """Muestra el menú interactivo"""
    print("\n" + "="*60)
    print("🗄️  SACV - SIMULADOR DE EVENTOS (VÍA POSTGRES)")
    print("="*60)
    print("\n📍 EVENTOS PREDEFINIDOS:")
    print("1. 🌍 Sismo en PICHINCHA (Magnitud 4.5)")
    print("2. 🌧️  Lluvia en ESMERALDAS (Inundaciones)")
    print("3. ⚡ Corte en LOJA (Mantenimiento UIDE)")
    print("4. 🌍 Sismo en AZUAY (Magnitud 5.2)")
    print("5. 🌧️  Lluvia en GUAYAS (Alerta Meteorológica)")
    print("6. ⚡ Corte en MANABI (Emergencia)")
    print("\n🔧 OPCIONES AVANZADAS:")
    print("7. ✏️  Evento Personalizado")
    print("\n0. ❌ Salir")
    print("="*60)


def evento_personalizado():
    """Permite crear un evento personalizado"""
    print("\n📝 CREAR EVENTO PERSONALIZADO")
    print("-" * 50)
    
    print("\nTipos disponibles: sismo, lluvia, corte")
    tipo = input("👉 Tipo de evento: ").lower().strip()
    
    print("\nProvincias disponibles:")
    print("AZUAY, BOLIVAR, CAÑAR, CARCHI, CHIMBORAZO, COTOPAXI")
    print("EL ORO, ESMERALDAS, GUAYAS, IMBABURA, LOJA, LOS RIOS")
    print("MANABI, PICHINCHA, SANTA ELENA, TUNGURAHUA")
    zona = input("\n👉 Zona (Provincia en MAYÚSCULAS): ").upper().strip()
    
    titulo = input("👉 Título del evento: ").strip()
    descripcion = input("👉 Descripción: ").strip()
    
    print("\nSeveridad: Alta, Media, Baja")
    severidad = input("👉 Severidad (default: Media): ").strip() or "Media"
    
    simular_evento_db(tipo, zona, titulo, descripcion, severidad)


def main():
    """Función principal"""
    while True:
        mostrar_menu()
        
        try:
            opcion = input("\n👉 Selecciona una opción: ").strip()
            
            if opcion == "0":
                print("\n👋 ¡Hasta luego!")
                break
            
            elif opcion == "1":
                simular_evento_db("sismo", "PICHINCHA", "SISMO DETECTADO", 
                                "Magnitud 4.5 - Epicentro norte de Quito - Revisión IGEPN", "Media")
            
            elif opcion == "2":
                simular_evento_db("lluvia", "ESMERALDAS", "LLUVIA FUERTE", 
                                "Inundaciones en sectores bajos - Alerta amarilla", "Alta")
            
            elif opcion == "3":
                simular_evento_db("corte", "LOJA", "CORTE DE ENERGÍA", 
                                "Mantenimiento programado UIDE - Sector centro", "Baja")
            
            elif opcion == "4":
                simular_evento_db("sismo", "AZUAY", "SISMO REGISTRADO", 
                                "Magnitud 5.2 en Cuenca - Sentido en toda la provincia", "Alta")
            
            elif opcion == "5":
                simular_evento_db("lluvia", "GUAYAS", "ALERTA METEOROLÓGICA", 
                                "Lluvias intensas en Guayaquil y zonas aledañas", "Media")
            
            elif opcion == "6":
                simular_evento_db("corte", "MANABI", "EMERGENCIA ELÉCTRICA", 
                                "Corte no programado en Portoviejo por falla técnica", "Alta")
            
            elif opcion == "7":
                evento_personalizado()
            
            else:
                print("\n⚠️  Opción no válida. Intenta de nuevo.")
            
            input("\n⏸️  Presiona ENTER para continuar...")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            input("\n⏸️  Presiona ENTER para continuar...")


if __name__ == "__main__":
    print("\n🔍 Verificando configuración...")
    print(f"   Base de datos: {os.getenv('DB_NAME')}")
    print(f"   Usuario: {os.getenv('DB_USER')}")
    print(f"   Host: localhost:5432")
    
    main()
