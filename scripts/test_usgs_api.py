#!/usr/bin/env python3
"""
Script de prueba para verificar que el USGS API funciona correctamente
"""
import requests
import json
from datetime import datetime

def test_usgs_api():
    print("🌍 Probando USGS Earthquake API para Ecuador...")
    print("="*60)
    
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    params = {
        "format": "geojson",
        "starttime": datetime.utcnow().strftime("%Y-%m-%d"),
        "minlatitude": -6.0,
        "maxlatitude": 2.0,
        "minlongitude": -82.0,
        "maxlongitude": -75.0,
        "minmagnitude": 4.0,
        "limit": 5,
        "orderby": "time"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"✅ HTTP Status: {response.status_code}")
        
        data = response.json()
        total = data.get('metadata', {}).get('count', 0)
        
        print(f"📊 Sismos encontrados hoy (>4.0): {total}")
        
        if total == 0:
            print("\n⚠️ No hay sismos >4.0 en Ecuador hoy")
            print("   Esto es NORMAL - significa que el API funciona correctamente")
            print("   pero no ha habido sismos significativos.")
            
            # Probar con rango de tiempo más amplio
            print("\n🔍 Probando últimos 7 días...")
            from datetime import timedelta
            params['starttime'] = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            total_week = data.get('metadata', {}).get('count', 0)
            print(f"📊 Sismos en últimos 7 días: {total_week}")
        
        if data.get('features'):
            print(f"\n📋 Últimos {min(5, len(data['features']))} sismos:")
            for i, event in enumerate(data['features'][:5], 1):
                props = event['properties']
                coords = event['geometry']['coordinates']
                
                timestamp = props['time'] / 1000
                fecha = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"\n  {i}. {props['place']}")
                print(f"     Magnitud: {props['mag']}")
                print(f"     Fecha: {fecha} UTC")
                print(f"     Profundidad: {coords[2]} km")
                print(f"     Coordenadas: {coords[1]}, {coords[0]}")
        
        print("\n✅ API del USGS funcionando correctamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_usgs_api()
