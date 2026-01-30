# Scripts - Sistema de Alertas Comunitarias

Este directorio contiene scripts útiles para probar y administrar el sistema.

## simulate_events.py

Script interactivo para simular eventos enviándolos a RabbitMQ (flujo completo del sistema).

### Uso

```bash
# Desde la raíz del proyecto
python scripts/simulate_events.py
```

### Requisitos

- Python 3.8+
- Librería `pika` instalada: `pip install pika`
- Docker Compose corriendo con RabbitMQ activo

---

## simulate_db.py

Script interactivo para simular eventos insertándolos **directamente en la base de datos** PostgreSQL.

### Uso

```bash
# Desde la raíz del proyecto
python scripts/simulate_db.py
```

### Requisitos

- Python 3.8+
- Librería `psycopg2-binary` instalada: `pip install psycopg2-binary`
- Librería `python-dotenv` instalada: `pip install python-dotenv`
- Docker Compose corriendo con PostgreSQL activo

### Ventajas

- ✅ **Sin dependencias de RabbitMQ**: Inserta directamente en la DB
- ✅ **Persistencia**: Los eventos quedan guardados en el historial
- ✅ **Verificación inmediata**: Puedes ver el evento en DBeaver al instante
- ✅ **Más simple**: Solo necesita acceso a PostgreSQL

---

## Funcionalidades Comunes

Ambos scripts ofrecen:

1. **Eventos Predefinidos**: 6 eventos listos para probar diferentes provincias
2. **Evento Personalizado**: Crea tus propios eventos de prueba
3. **Menú Interactivo**: Fácil de usar

---

## Flujo de Prueba Recomendado

1. Suscríbete a una provincia en el bot de Telegram (`/start`)
2. Ejecuta uno de los simuladores:
   - `simulate_events.py` - Para probar el flujo completo (RabbitMQ → Notifier)
   - `simulate_db.py` - Para insertar directamente en la base de datos
3. Selecciona un evento para esa provincia
4. Verifica que recibes la notificación en Telegram

---

## Ejemplo de Uso (simulate_db.py)

```
🗄️  SACV - SIMULADOR DE EVENTOS (VÍA POSTGRES)
============================================================

📍 EVENTOS PREDEFINIDOS:
1. 🌍 Sismo en PICHINCHA (Magnitud 4.5)
2. 🌧️  Lluvia en ESMERALDAS (Inundaciones)
3. ⚡ Corte en LOJA (Mantenimiento UIDE)
...

👉 Selecciona una opción: 2

✅ [ÉXITO] Evento insertado en la base de datos
   📋 Título: LLUVIA FUERTE
   📍 Zona: ESMERALDAS
   🎯 Tipo: lluvia
   🆔 Event ID: a1b2c3d4-...

💡 Verifica en DBeaver la tabla 'events' para ver el registro
💡 Si estás suscrito a ESMERALDAS, deberías recibir una notificación en Telegram
```

---

## Troubleshooting

**Error de conexión a RabbitMQ:**
```bash
# Verifica que Docker esté corriendo
docker-compose ps

# Verifica logs de RabbitMQ
docker-compose logs rabbitmq
```

**No recibes notificaciones:**
1. Verifica que el bot esté corriendo: `docker-compose logs telegram-bot`
2. Verifica que el notifier esté corriendo: `docker-compose logs notifier`
3. Verifica tu suscripción en la base de datos:
   ```sql
   SELECT * FROM subscriptions WHERE active = true;
   ```
