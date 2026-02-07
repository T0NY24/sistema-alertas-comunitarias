# 🤖 Guía de Suscripción al Bot de Telegram

## 📱 Cómo recibir notificaciones en Telegram

### Paso 1: Buscar el Bot

1. Abre Telegram en tu celular o computadora
2. Busca: **@AlertasComunitariasAnthonyBot**
3. O usa este link directo: https://t.me/AlertasComunitariasAnthonyBot

### Paso 2: Iniciar el Bot

1. Presiona el botón **"INICIAR"** o **"START"**
2. Verás un mensaje de bienvenida con 2 opciones:
   - 🚀 **Configurar mis Alertas** ← Presiona este
   - ❌ Salir / Cancelar

### Paso 3: Seleccionar tu Provincia

1. Se mostrará un menú con las 24 provincias de Ecuador
2. Opciones disponibles:
   - 🇪🇨 **TODO ECUADOR** (Solo emergencias nacionales de alta severidad)
   - 📍 Provincias individuales (Ej: Pichincha, Guayas, Loja, etc.)

3. **Selecciona tu provincia** presionando el botón correspondiente

### Paso 4: Confirmación

Verás un mensaje que dice:

```
✅ Suscripción Guardada
Provincia: [Tu Provincia] (ID: X)

Recibirás alertas automáticas para esta zona.
```

### Paso 5: Probar las Notificaciones

1. Desde el simulador en el admin-panel, crea un evento
2. Asegúrate de:
   - ✅ Seleccionar la **misma provincia** a la que te suscribiste
   - ✅ Marcar el evento como **"CONFIRMADO"**
   - ✅ Elegir una severidad (ALTA, MEDIA, o BAJA)

3. En **menos de 5 segundos** deberías recibir la notificación en Telegram

---

## 🔧 Comandos Disponibles

- `/start` - Menú principal y configuración
- `/help` - Ayuda y soporte

---

## 🔄 Cambiar de Provincia

1. Escribe `/start` nuevamente
2. Presiona **"Configurar mis Alertas"**
3. Selecciona una nueva provincia
4. ¡Listo! Tu suscripción se actualiza automáticamente

---

## ❌ Cancelar Alertas

1. Escribe `/start`
2. Presiona **"Configurar mis Alertas"**
3. Selecciona tu provincia actual
4. Presiona **"❌ Cancelar Alertas"**

---

## 🧪 Script de Prueba Masiva

Para probar las notificaciones en las 24 provincias:

```bash
# En el VPS
cd ~/sistema-alertas
python3 scripts/simulate_24_provinces.py
```

Este script:
- ✅ Crea un evento de prueba para cada provincia
- ✅ Varía el tipo de evento (SISMO, LLUVIA, CORTE_LUZ)
- ✅ Todos los eventos son marcados como CONFIRMADOS
- ✅ Envía notificaciones automáticamente

---

## 🐛 Troubleshooting

### No recibo notificaciones

1. **Verifica tu suscripción:**
   ```sql
   -- En el VPS, ejecuta:
   docker exec -i sacv_postgres psql -U sacv_user -d sacv_db -c \
   "SELECT * FROM subscriptions WHERE active = true;"
   ```

2. **Verifica que el bot esté corriendo:**
   ```bash
   docker-compose logs telegram-bot | tail -20
   ```

3. **Verifica que el notifier esté corriendo:**
   ```bash
   docker-compose logs notifier | tail -20
   ```

4. **Verifica RabbitMQ:**
   - Abre: http://217.216.67.99:15673
   - Usuario: `sacv`
   - Password: `rabbitmq_secure_password_2026`
   - Verifica que la cola `confirmed_events` tenga mensajes

### El bot no responde

```bash
# Reiniciar el bot
docker-compose restart telegram-bot

# Ver logs en tiempo real
docker-compose logs -f telegram-bot
```

---

## 📊 Verificar que llegó la notificación

Después de crear un evento CONFIRMADO:

1. **Telegram:** Deberías recibir un mensaje en menos de 5 segundos
2. **Base de datos:** Verifica que se guardó la notificación:
   ```sql
   docker exec -i sacv_postgres psql -U sacv_user -d sacv_db -c \
   "SELECT * FROM notifications ORDER BY sent_at DESC LIMIT 5;"
   ```

---

## 🎯 Información Importante

- **Solo eventos CONFIRMADOS** envían notificaciones
- **Alertas Nacionales** (provincia_id = 0) solo envían eventos de severidad ALTA o MEDIA
- **Provincias específicas** reciben todos los eventos (ALTA, MEDIA, BAJA)
- Las notificaciones se envían **automáticamente** vía RabbitMQ

---

## 🧑‍💻 Token del Bot

El token actual es: `8503136374:AAE2Nsu1r08R3dhLNr4tMBNzBbIM6kOEjtc`

Este token está configurado en `.env` como `TELEGRAM_BOT_TOKEN`.

---

¡Listo! 🎉 Ahora estás suscrito y recibirás alertas en tiempo real.
