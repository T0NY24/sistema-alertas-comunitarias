#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la estructura del sitio web del IGEPN
"""
import requests
from bs4 import BeautifulSoup
import json

def test_url(url):
    print(f"\n{'='*60}")
    print(f"🌍 Probando: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print(f"✅ HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar tablas
        tablas = soup.find_all('table')
        print(f"📊 Tablas encontradas: {len(tablas)}")
        
        if tablas:
            for idx, tabla in enumerate(tablas[:3]):
                print(f"\n  📋 Tabla {idx + 1}:")
                rows = tabla.find_all('tr')
                print(f"     Filas: {len(rows)}")
                
                if len(rows) > 1:
                    # Mostrar encabezados
                    headers = rows[0].find_all(['th', 'td'])
                    if headers:
                        print(f"     Encabezados: {[h.text.strip()[:20] for h in headers]}")
                    
                    # Mostrar primera fila de datos
                    cols = rows[1].find_all('td')
                    if cols:
                        print(f"     Primera fila ({len(cols)} columnas):")
                        for i, col in enumerate(cols[:7]):
                            print(f"       [{i}] {col.text.strip()[:50]}")
                        return True
        
        # Buscar divs con datos
        divs_sismo = soup.find_all('div', class_=lambda x: x and 'sismo' in str(x).lower())
        print(f"\n📦 Divs con 'sismo': {len(divs_sismo)}")
        
        # Buscar scripts con datos JSON
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'sismo' in script.string.lower():
                print(f"\n💾 Script con datos de sismo encontrado")
                print(f"   Primeros 200 chars: {script.string[:200]}")
                break
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    urls_to_test = [
        'https://www.igepn.edu.ec/ultimos-sismos',
        'https://www.igepn.edu.ec/servicios/ultimo-sismo',
        'https://www.igepn.edu.ec/portal/ultimo-sismo/ultimo-sismo.html',
        'https://www.igepn.edu.ec/servicios/noticias',
    ]
    
    print("\n🔍 DIAGNÓSTICO DEL SCRAPER IGEPN")
    print("="*60)
    
    for url in urls_to_test:
        if test_url(url):
            print(f"\n✅ ¡URL FUNCIONAL ENCONTRADA!: {url}")
            break
    else:
        print("\n❌ Ninguna URL funcionó. El IGEPN puede haber cambiado su estructura.")
        print("💡 Sugerencia: Visita https://www.igepn.edu.ec manualmente para encontrar la sección de sismos.")
