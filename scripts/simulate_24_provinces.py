#!/usr/bin/env python3
"""
Simulador de Eventos Masivos - 24 Provincias
Envía un evento de prueba a cada una de las 24 provincias de Ecuador
"""
import requests
import sys
from datetime import datetime

# Configuración
API_URL = "http://217.216.67.99:8001/api/events"

# Las 24 provincias de Ecuador con sus IDs
PROVINCIAS = {
    1: "Azuay", 2: "Bolívar", 3: "Cañar", 4: "Carchi", 5: "Chimborazo",
    6: "Cotopaxi", 7: "El Oro", 8: "Esmeraldas", 9: "Galápagos", 10: "Guayas",
    11: "Imbabura", 12: "Loja", 13: "Los Ríos", 14: "Manabí", 15: "Morona Santiago",
    16: "Napo", 17: "Orellana", 18: "Pastaza", 19: "Pichincha", 20: "Santa Elena",
    21: "Santo Domingo de los Tsáchilas", 22: "Sucumbíos", 23: "Tungurahua", 24: "Zamora Chinchipe"
}

# Tipos de eventos para variar
EVENTOS = [
    {"type": "SISMO", "severity": "ALTA", "icon": "🌋"},
    {"type": "LLUVIA", "severity": "MEDIA", "icon": "🌧️"},
    {"type": "CORTE_LUZ", "severity": "BAJA", "icon": "⚡"}
]

def crear_evento(province_id, province_name):
    """Crea un evento de prueba para una provincia específica"""
    # Rotar tipos de eventos
    evento_tipo = EVENTOS[province_id % len(EVENTOS)]
    
    evento = {
        "type": evento_tipo["type"],
        "severity": evento_tipo["severity"],
        "zone": province_name,
        "province_id": province_id,
        "title": f"{evento_tipo['icon']} {evento_tipo['type']} en {province_name}",
        "description": f"Evento de prueba generado automáticamente para {province_name}. Severidad: {evento_tipo['severity']}",
        "evidence_url": "https://ejemplo.com/prueba",
        "status": "CONFIRMADO"  # Importante: debe ser CONFIRMADO para que envíe notificaciones
    }
    
    try:
        response = requests.post(API_URL, json=evento, timeout=10)
        if response.status_code == 201:
            print(f"✅ [{province_id:2d}] {province_name:30s} - {evento_tipo['icon']} {evento_tipo['type']}")
            return True
        else:
            print(f"❌ [{province_id:2d}] {province_name:30s} - Error {response.status_code}: {response.text[:50]}")
            return False
    except Exception as e:
        print(f"❌ [{province_id:2d}] {province_name:30s} - Error de conexión: {str(e)[:50]}")
        return False

def main():
    print("=" * 80)
    print("🚀 SIMULADOR DE EVENTOS MASIVOS - 24 PROVINCIAS DEL ECUADOR")
    print("=" * 80)
    print(f"\n⏰ Iniciando simulación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 API Endpoint: {API_URL}")
    print(f"📊 Total de provincias: {len(PROVINCIAS)}\n")
    
    exitos = 0
    fallos = 0
    
    for province_id, province_name in PROVINCIAS.items():
        if crear_evento(province_id, province_name):
            exitos += 1
        else:
            fallos += 1
    
    print("\n" + "=" * 80)
    print(f"📈 RESUMEN:")
    print(f"   ✅ Eventos creados exitosamente: {exitos}")
    print(f"   ❌ Fallos: {fallos}")
    print(f"   📊 Total procesados: {exitos + fallos}")
    print("=" * 80)
    
    if fallos > 0:
        print("\n⚠️  Algunas provincias fallaron. Verifica los logs del API Gateway.")
        sys.exit(1)
    else:
        print("\n🎉 ¡Todos los eventos fueron creados exitosamente!")
        print("📱 Verifica tu Telegram para recibir las notificaciones.")
        sys.exit(0)

if __name__ == "__main__":
    main()
