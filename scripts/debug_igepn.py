import requests
from bs4 import BeautifulSoup
import json

def test_igepn():
    url = "https://www.igepn.edu.ec/servicios/ultimo-sismo"
    print(f"🌍 Conectando a {url}...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Intentamos encontrar la tabla
        print("🔍 Buscando tabla de sismos...")
        
        # Estrategia 1: Buscar por ID 'sismo_table' (La que pusimos en el SQL)
        tabla = soup.find('table', id='sismo_table') # A veces el IGEPN usa este ID
        
        # Estrategia 2: Buscar la primera tabla genérica con clase 'table'
        if not tabla:
             print("⚠️ No encontré id='sismo_table', buscando tablas genéricas...")
             tablas = soup.find_all('table')
             if tablas:
                 tabla = tablas[0]
                 print(f"✅ Encontré una tabla genérica ({len(tablas)} tablas en total).")
        
        if not tabla:
            print("❌ ERROR CRÍTICO: No se encontró ninguna tabla en el HTML.")
            # Opcional: imprimir un pedazo del HTML para ver qué hay
            print("\n📄 Primeros 1000 caracteres del HTML:")
            print(soup.prettify()[:1000])
            return

        # Intentar leer la primera fila de datos
        rows = tabla.find_all('tr')
        print(f"📊 La tabla tiene {len(rows)} filas.")
        
        if len(rows) > 1:
            cols = rows[1].find_all('td')
            if len(cols) >= 5:
                datos = [c.text.strip() for c in cols]
                print("\n✅ DATOS ENCONTRADOS (Último sismo):")
                print(f"📅 Fecha: {datos[0]}")
                print(f"📍 Lat/Long: {datos[1]}, {datos[2]}")
                print(f"📉 Profundidad: {datos[3]}")
                print(f"💥 Magnitud: {datos[4]}")
                print(f"🗺️ Zona: {datos[5] if len(datos) > 5 else 'N/A'}")
                
                # Mostrar el payload que se generaría
                print("\n📦 Payload que se enviaría:")
                payload = {
                    "date": datos[0],
                    "latitude": datos[1],
                    "longitude": datos[2],
                    "depth": datos[3],
                    "magnitude": datos[4],
                    "zone_raw": datos[5] if len(datos) > 5 else "Ecuador",
                    "source": "IGEPN"
                }
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print(f"⚠️ La fila tiene solo {len(cols)} columnas, esperaba al menos 5")
        else:
            print("❌ La tabla existe pero está vacía o solo tiene encabezados.")

    except Exception as e:
        print(f"❌ Error de ejecución: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_igepn()
