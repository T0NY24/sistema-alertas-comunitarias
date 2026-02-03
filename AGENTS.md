# AGENTS.md - Sistema de Alertas Comunitarias Verificadas (SACV)

> **Propósito**: Este documento está diseñado para que cualquier agente de IA (Jules, Copilot, Claude, etc.) comprenda completamente el proyecto SACV y pueda asistir efectivamente en su desarrollo, mantenimiento y debugging.

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Base de Datos](#base-de-datos)
4. [Microservicios](#microservicios)
5. [Flujo de Datos](#flujo-de-datos)
6. [Configuración y Despliegue](#configuración-y-despliegue)
7. [Telegram Bot](#telegram-bot)
8. [API REST](#api-rest)
9. [Guía de Debugging](#guía-de-debugging)
10. [Convenciones del Código](#convenciones-del-código)

---

## 🎯 Resumen Ejecutivo

### ¿Qué es SACV?

**Sistema de Alertas Comunitarias Verificadas** es una plataforma de microservicios que:

1. **Captura** eventos de fuentes oficiales ecuatorianas (sismos, clima, cortes de energía)
2. **Normaliza** los datos a un esquema común
3. **Verifica** la confianza mediante un sistema de scoring (0-100)
4. **Notifica** a usuarios suscritos vía Telegram cuando hay eventos confirmados

### Tecnologías Core

- **Lenguaje**: Python 3.11+
- **Framework Web**: FastAPI
- **Base de Datos**: PostgreSQL 15
- **Message Broker**: RabbitMQ 3.12
- **Cache**: Redis 7
- **Containerización**: Docker + Docker Compose
- **Logging**: Structlog (JSON estructurado)
- **Telegram**: python-telegram-bot 20.7+

### Estado Actual

- **Versión**: 1.0 MVP
- **Estado**: Funcional y Validado ✅
- **Completitud**: ~67%
- **Servicios Activos**: 8 contenedores Docker

---

## 🏗️ Arquitectura del Sistema

### Patrón Arquitectónico

**Event-Driven Microservices Architecture** con las siguientes características:

- **Pub/Sub**: RabbitMQ con 3 queues principales
- **Event Sourcing**: Almacenamiento inmutable de `raw_events`
- **CQRS**: Separación de escritura (eventos) y lectura (API)
- **Resilience**: Retry logic, rate limiting, health checks

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│              Fuentes Oficiales Ecuatorianas              │
│         IGEPN          INAMHI          CNEL             │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP Scraping
                 ▼
         ┌───────────────┐
         │    Scraper    │──► PostgreSQL (raw_events)
         │   Service     │──► Redis (rate limiting)
         └───────┬───────┘
                 │ RabbitMQ: raw_events
                 ▼
         ┌───────────────┐
         │  Normalizer   │──► PostgreSQL (events)
         │   Service     │
         └───────┬───────┘
                 │ RabbitMQ: normalized_events
                 ▼
         ┌───────────────┐
         │   Verifier    │──► PostgreSQL (update score/status)
         │   Service     │
         └───────┬───────┘
                 │ RabbitMQ: confirmed_events
                 ▼
         ┌───────────────┐
         │   Notifier    │──► Telegram Bot API
         │   Service     │──► PostgreSQL (notifications)
         └───────────────┘
                 │
                 ▼
           👥 Usuarios
```

### Servicios Docker

| Servicio | Contenedor | Puerto | Descripción |
|----------|-----------|--------|-------------|
| **postgres** | `sacv_postgres` | 5432 | Base de datos principal |
| **redis** | `sacv_redis` | 6379 | Cache y rate limiting |
| **rabbitmq** | `sacv_rabbitmq` | 5672, 15672 | Message broker + UI |
| **scraper** | `sacv_scraper` | - | Captura eventos de fuentes |
| **normalizer** | `sacv_normalizer` | - | Transforma a schema común |
| **verifier** | `sacv_verifier` | - | Calcula score de confianza |
| **notifier** | `sacv_notifier` | - | Envía notificaciones Telegram |
| **telegram-bot** | `sacv_telegram_bot` | - | Maneja interacciones del bot |
| **api-gateway** | `sacv_api` | 8000 | REST API pública |

---

## 🗄️ Base de Datos

### Schema PostgreSQL

#### Tabla: `sources`

Fuentes oficiales configuradas para scraping.

```sql
CREATE TABLE sources (
    source_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    base_url TEXT NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('sismo', 'lluvia', 'corte')),
    domain VARCHAR(255) NOT NULL,
    parser_config JSONB NOT NULL,
    frequency_sec INTEGER NOT NULL DEFAULT 300,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos Clave**:
- `type`: Tipo de evento que genera la fuente
- `parser_config`: Configuración JSON para el scraper específico
- `frequency_sec`: Frecuencia de scraping en segundos

#### Tabla: `raw_events`

Eventos crudos capturados (inmutables).

```sql
CREATE TABLE raw_events (
    raw_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(source_id),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload JSONB NOT NULL,
    raw_hash VARCHAR(64) UNIQUE NOT NULL
);
```

**Campos Clave**:
- `raw_payload`: JSON completo del evento capturado
- `raw_hash`: SHA256 para deduplicación

#### Tabla: `events`

Eventos normalizados y verificados.

```sql
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,
    occurred_at TIMESTAMP NOT NULL,
    zone VARCHAR(255),
    severity VARCHAR(50),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    evidence_url TEXT,
    source_id UUID REFERENCES sources(source_id),
    dedup_hash VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'NO_VERIFICADO' CHECK (
        status IN ('CONFIRMADO', 'EN_VERIFICACION', 'NO_VERIFICADO')
    ),
    score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos Clave**:
- `status`: Estado de verificación (CONFIRMADO >= 70 score)
- `score`: Puntuación de confianza (0-100)
- `dedup_hash`: Hash para evitar duplicados

#### Tabla: `users`

Usuarios del sistema.

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'operator', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: `subscriptions`

Suscripciones de usuarios a alertas.

```sql
CREATE TABLE subscriptions (
    sub_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    province_id INTEGER NOT NULL,
    type VARCHAR(50),
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('telegram', 'email', 'whatsapp')),
    channel_id VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, province_id)
);
```

**Campos Clave**:
- `province_id`: ID numérico de la provincia (1-24)
- `channel_id`: Para Telegram es el `chat_id`
- `UNIQUE(channel_id, province_id)`: Un usuario puede tener múltiples suscripciones a diferentes provincias

**Provincias de Ecuador** (1-24):
```python
PROVINCIAS = {
    "1": "AZUAY", "2": "BOLIVAR", "3": "CAÑAR", "4": "CARCHI", 
    "5": "COTOPAXI", "6": "CHIMBORAZO", "7": "EL ORO", "8": "ESMERALDAS", 
    "9": "GUAYAS", "10": "IMBABURA", "11": "LOJA", "12": "LOS RIOS", 
    "13": "MANABI", "14": "MORONA SANTIAGO", "15": "NAPO", "16": "PASTAZA", 
    "17": "PICHINCHA", "18": "TUNGURAHUA", "19": "ZAMORA CHINCHIPE", 
    "20": "GALAPAGOS", "21": "SUCUMBIOS", "22": "ORELLANA", 
    "23": "STO. DOMINGO", "24": "SANTA ELENA"
}
```

#### Tabla: `notifications`

Registro de notificaciones enviadas.

```sql
CREATE TABLE notifications (
    notif_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES events(event_id),
    sub_id UUID REFERENCES subscriptions(sub_id),
    channel VARCHAR(50) NOT NULL,
    to_address VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    error_message TEXT
);
```

**Orden de Columnas** (IMPORTANTE para INSERTs):
```
notif_id, event_id, sub_id, channel, to_address, sent_at, status, error_message
```

#### Tabla: `verification_rules`

Reglas de scoring para verificación.

```sql
CREATE TABLE verification_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    weight INTEGER NOT NULL,
    enabled BOOLEAN DEFAULT true
);
```

**Reglas por Defecto**:
1. Dominio en lista blanca: **40 puntos**
2. Evidencia URL válida: **15 puntos**
3. Timestamp reciente (<24h): **15 puntos**
4. Campos completos: **10 puntos**
5. Corroboración cruzada: **20 puntos**

**Total Máximo**: 100 puntos

---

## 🔧 Microservicios

### 1. Scraper Service

**Ubicación**: `services/scraper/src/main.py`

**Responsabilidades**:
- Ejecutar scraping programado de fuentes oficiales
- Aplicar rate limiting (Redis)
- Guardar eventos crudos en `raw_events`
- Publicar a queue `raw_events`

**Componentes**:
```python
class ScraperService:
    def __init__(self):
        self.db_conn = None
        self.redis_client = None
        self.rabbitmq_conn = None
        self.scheduler = BlockingScheduler()
        self.scrapers = {
            'sismo': IGEPNScraper,
            'lluvia': InamhiScraper,
            'corte': CnelScraper
        }
```

**Scrapers Específicos**:

1. **IGEPNScraper** (`services/scraper/src/scrapers/igepn_scraper.py`)
   - Fuente: Instituto Geofísico del Ecuador
   - URL: https://www.igepn.edu.ec/servicios/ultimo-sismo
   - Tipo: `sismo`
   - Método: BeautifulSoup (HTML parsing)

2. **InamhiScraper** (`services/scraper/src/scrapers/inamhi_scraper.py`)
   - Fuente: INAMHI
   - Tipo: `lluvia`
   - Método: Playwright (JavaScript rendering)

3. **CnelScraper** (`services/scraper/src/scrapers/cnel_scraper.py`)
   - Fuente: CNEL
   - Tipo: `corte`
   - Método: BeautifulSoup

**Flujo de Ejecución**:
```
1. Scheduler ejecuta scrape_source() cada N segundos
2. Verificar rate limit en Redis
3. Ejecutar scraper específico
4. Generar raw_hash (SHA256)
5. Guardar en raw_events (ON CONFLICT DO NOTHING)
6. Publicar a RabbitMQ queue 'raw_events'
7. Setear rate limit en Redis (60 segundos)
```

**Variables de Entorno**:
```bash
DATABASE_URL=postgresql://sacv_user:password@postgres:5432/sacv_db
REDIS_URL=redis://redis:6379
RABBITMQ_URL=amqp://sacv:password@rabbitmq:5672
```

---

### 2. Normalizer Service

**Ubicación**: `services/normalizer/src/main.py`

**Responsabilidades**:
- Consumir eventos de queue `raw_events`
- Transformar a schema normalizado
- Extraer zona geográfica y severidad
- Generar `dedup_hash`
- Guardar en tabla `events`
- Publicar a queue `normalized_events`

**Lógica de Normalización**:

```python
def normalize_event(self, raw_event):
    # 1. Obtener tipo de la fuente
    event_type = get_source_type(raw_event['source_id'])
    
    # 2. Parsear fecha
    occurred_at = parse_occurred_at(raw_payload.get('date'))
    
    # 3. Extraer zona (provincia)
    zone = extract_zone(raw_payload)  # Busca keywords en contenido
    
    # 4. Extraer severidad
    severity = extract_severity(raw_payload)  # Alta/Media/Baja
    
    # 5. Generar dedup_hash
    dedup_hash = sha256(f"{type}_{zone}_{date}")
    
    # 6. Validar con Pydantic
    validated = NormalizedEvent(**data)
    
    return validated.dict()
```

**Extracción de Zona**:
```python
provincias = {
    'pichincha': 'Pichincha',
    'quito': 'Pichincha',
    'guayas': 'Guayas',
    'guayaquil': 'Guayas',
    # ... etc
}
# Busca keywords en title + content
```

**Extracción de Severidad**:
```python
high_keywords = ['fuerte', 'intenso', 'severo', 'grave', 'critico']
medium_keywords = ['moderado', 'medio', 'considerable']
# Retorna: 'Alta', 'Media', 'Baja'
```

**INSERT en events**:
```sql
INSERT INTO events (
    type, occurred_at, zone, severity, title, description,
    evidence_url, source_id, dedup_hash, status, score
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'NO_VERIFICADO', 0)
ON CONFLICT (dedup_hash) DO UPDATE
SET updated_at = CURRENT_TIMESTAMP
RETURNING event_id
```

---

### 3. Verifier Service

**Ubicación**: `services/verifier/src/main.py`

**Responsabilidades**:
- Consumir eventos de queue `normalized_events`
- Aplicar reglas de scoring
- Calcular score total (0-100)
- Determinar status (CONFIRMADO/EN_VERIFICACION/NO_VERIFICADO)
- Actualizar evento en BD
- Si CONFIRMADO, publicar a queue `confirmed_events`

**Sistema de Scoring**:

```python
class VerificationRules:
    def calculate_score(self, event):
        score = 0
        
        # R1: Dominio en lista blanca (40 pts)
        if self.check_domain_whitelist(event['source_id']):
            score += 40
        
        # R2: URL válida (15 pts)
        if self.validate_url(event['evidence_url']):
            score += 15
        
        # R3: Timestamp reciente <24h (15 pts)
        if self.is_recent(event['occurred_at']):
            score += 15
        
        # R4: Campos completos (10 pts)
        if self.check_completeness(event):
            score += 10
        
        # R5: Corroboración cruzada (20 pts)
        if self.check_cross_reference(event):
            score += 20
        
        return min(score, 100)
    
    def determine_status(self, score):
        if score >= 70:
            return 'CONFIRMADO'
        elif score >= 40:
            return 'EN_VERIFICACION'
        else:
            return 'NO_VERIFICADO'
```

**UPDATE en events**:
```sql
UPDATE events
SET score = %s,
    status = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE event_id = %s
RETURNING event_id
```

---

### 4. Notifier Service

**Ubicación**: `services/notifier/src/main.py`

**Responsabilidades**:
- Consumir eventos de queue `confirmed_events`
- Obtener suscripciones activas para el evento
- Enviar notificaciones vía Telegram
- Registrar en tabla `notifications`

**Flujo de Notificación**:

```python
async def process_event(self, event):
    event_id = event.get('event_id')
    province_id = event.get('province_id')
    
    # 1. Obtener suscripciones activas
    subs = self.get_subscriptions(event)
    
    # 2. Para cada suscripción
    for sub in subs:
        try:
            # 3. Enviar mensaje Telegram
            await self.send_telegram_msg(sub['channel_id'], event)
            
            # 4. Registrar notificación exitosa
            self.save_notification(
                sub['sub_id'], 
                event_id, 
                sub['channel_id'], 
                'sent'
            )
        except Exception as e:
            # 5. Registrar error
            self.save_notification(
                sub['sub_id'], 
                event_id, 
                sub['channel_id'], 
                'failed', 
                str(e)
            )
```

**Query de Suscripciones**:
```sql
SELECT s.sub_id, s.channel_id
FROM subscriptions s
WHERE s.active = true
  AND s.province_id = %s
  AND (s.type = %s OR s.type IS NULL)
```

**Formato de Mensaje Telegram**:
```python
mensaje = (
    f"🚨 *ALERTA: {event.get('type', 'EVENTO').upper()}*\n\n"
    f"📍 *Provincia:* {province_name}\n"
    f"📝 *Detalle:* {event.get('description')}\n"
    f"📅 *Fecha:* {timestamp}"
)
```

**INSERT en notifications**:
```sql
INSERT INTO notifications (
    notif_id, event_id, sub_id, channel, to_address, 
    sent_at, status, error_message
)
VALUES (%s, %s, %s, 'telegram', %s, CURRENT_TIMESTAMP, %s, %s)
```

**IMPORTANTE**: El orden de columnas debe ser exacto. `sent_at` usa `CURRENT_TIMESTAMP`.

---

### 5. Telegram Bot Service

**Ubicación**: `services/notifier/src/telegram_bot.py`

**Responsabilidades**:
- Manejar comandos del bot (`/start`, `/suscribir`, `/ayuda`)
- Gestionar suscripciones de usuarios
- Procesar callbacks de botones inline

**Comandos Disponibles**:

1. **`/start`**
   - Muestra menú de provincias
   - Permite suscribirse a una provincia

2. **`/suscribir`**
   - Alias de `/start`

3. **`/ayuda`**
   - Muestra información del bot

**Handlers**:

```python
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Comandos
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("suscribir", suscribir_command))
application.add_handler(CommandHandler("ayuda", ayuda_command))

# Callbacks de botones
application.add_handler(CallbackQueryHandler(handle_callback))

# Iniciar polling
application.run_polling()
```

**Subscription Handler** (`services/notifier/src/subscription_handler.py`):

```python
PROVINCIAS = {
    "1": "AZUAY", "2": "BOLIVAR", "3": "CAÑAR", # ... 24 provincias
}

def crear_teclado_provincias():
    """Genera teclado inline con botones de provincias"""
    keyboard = []
    ids = sorted(PROVINCIAS.keys(), key=int)
    
    for i in range(0, len(ids), 2):
        row = [
            InlineKeyboardButton(
                PROVINCIAS[ids[i]], 
                callback_data=f"sub_{ids[i]}"
            )
        ]
        if i + 1 < len(ids):
            row.append(
                InlineKeyboardButton(
                    PROVINCIAS[ids[i+1]], 
                    callback_data=f"sub_{ids[i+1]}"
                )
            )
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)
```

**Manejo de Suscripción**:

```python
async def manejar_callback_suscripcion(update, context, db_conn):
    query = update.callback_query
    data = query.data
    chat_id = str(query.message.chat_id)
    
    if data.startswith("sub_"):
        prov_id = data.split("_")[1]  # Ej: "17"
        nombre_provincia = PROVINCIAS.get(prov_id)
        
        cursor = db_conn.cursor()
        try:
            # 1. Obtener dinámicamente el primer usuario disponible
            cursor.execute("SELECT user_id FROM users LIMIT 1")
            row = cursor.fetchone()
            if not row:
                await query.edit_message_text("❌ Error: No hay usuarios en la tabla 'users'.")
                return
            user_id = row[0]
            
            # 2. UPSERT: Inserta o actualiza según el channel_id
            # IMPORTANTE: ON CONFLICT ahora es solo por channel_id
            cursor.execute("""
                INSERT INTO subscriptions (
                    sub_id, user_id, province_id, channel_id, active, channel
                )
                VALUES (%s, %s, %s, %s, true, 'telegram')
                ON CONFLICT (channel_id) 
                DO UPDATE SET 
                    province_id = EXCLUDED.province_id,
                    active = true;
            """, (str(uuid.uuid4()), user_id, int(prov_id), chat_id))
            
            db_conn.commit()
            
            # 3. Confirmar al usuario
            keyboard = [
                [InlineKeyboardButton("🔄 Cambiar Provincia", callback_data="ir_menu")],
                [InlineKeyboardButton("❌ Cancelar Alertas", callback_data="cancelar_todo")]
            ]
            await query.edit_message_text(
                text=f"✅ *Suscripción Guardada*\n\n"
                     f"Provincia: `{nombre_provincia}` (ID: {prov_id})\n\n"
                     f"Recibirás alertas automáticas para esta zona.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
            # 4. Logging para debugging
            logger.info(f"Suscripción exitosa: Chat {chat_id} -> Provincia {prov_id}")
            print(f"✅ DEBUG: Suscripción guardada - Chat: {chat_id}, Provincia: {prov_id}")
            
        except Exception as e:
            db_conn.rollback()
            logger.error(f"Error crítico en DB: {e}")
            print(f"❌ DEBUG_ERROR: {e}")  # Imprime error real en Docker logs
            await query.edit_message_text(
                f"❌ Error al guardar en base de datos.\nDetalle: {str(e)[:50]}..."
            )
        finally:
            cursor.close()
```

**Cambios Importantes en la Lógica de Suscripción**:

1. **User ID Dinámico**: Ya no usa subquery `(SELECT user_id FROM users LIMIT 1)` directamente en el INSERT. Primero obtiene el `user_id` y valida que exista.

2. **ON CONFLICT Simplificado**: 
   - **Antes**: `ON CONFLICT (channel_id, province_id)`
   - **Ahora**: `ON CONFLICT (channel_id)`
   - Esto permite que un usuario cambie de provincia sin crear múltiples registros

3. **Debug Logging**: Añadido `print()` statements para facilitar debugging en Docker logs

4. **Validación de Usuario**: Si no hay usuarios en la tabla, muestra error al usuario en lugar de fallar silenciosamente

**Callbacks Disponibles**:
- `sub_{province_id}`: Suscribirse a provincia
- `ir_menu`: Volver al menú de provincias
- `cancelar_todo`: Desactivar todas las alertas

---

### 6. API Gateway Service

**Ubicación**: `services/api-gateway/src/main.py`

**Framework**: FastAPI

**Endpoints Disponibles**:

#### Health & Info

```python
GET /
# Respuesta: {"message": "SACV API v1.0", "status": "running"}

GET /health
# Respuesta: {"status": "healthy", "database": "healthy"}
```

#### Eventos Crudos

```python
GET /api/raw-events?limit=10&offset=0
# Respuesta: List[RawEventResponse]

GET /api/raw-events/{raw_id}
# Respuesta: Detalle completo del raw_event
```

#### Eventos Normalizados

```python
GET /api/events?type=sismo&zone=Pichincha&status=CONFIRMADO&limit=50
# Respuesta: List[EventResponse]

GET /api/events/{event_id}
# Respuesta: EventResponse
```

#### Fuentes

```python
GET /api/sources?active_only=true
# Respuesta: List[SourceResponse]
```

#### Estadísticas

```python
GET /api/stats
# Respuesta:
{
  "total_sources": 3,
  "active_sources": 3,
  "total_raw_events": 150,
  "total_events": 120,
  "events_by_status": {
    "confirmados": 45,
    "en_verificacion": 30,
    "no_verificados": 45
  },
  "last_scraping": "2026-01-30T22:00:00"
}
```

**Documentación Interactiva**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**CORS**: Configurado para permitir todos los orígenes (en producción, restringir).

---

## 🔄 Flujo de Datos Completo

### Secuencia de Eventos

```mermaid
sequenceDiagram
    participant S as Scraper
    participant MQ as RabbitMQ
    participant N as Normalizer
    participant V as Verifier
    participant NT as Notifier
    participant DB as PostgreSQL
    participant TG as Telegram

    Note over S: Ejecución programada (cada 300s)
    S->>S: Fetch página oficial
    S->>DB: INSERT INTO raw_events
    S->>MQ: Publish(raw_events)
    
    MQ->>N: Consume raw_event
    N->>N: Transform to schema
    N->>N: Generate dedup_hash
    N->>DB: INSERT INTO events
    N->>MQ: Publish(normalized_events)
    
    MQ->>V: Consume normalized
    V->>V: Apply scoring rules
    V->>DB: Check domain whitelist
    V->>V: Calculate score
    V->>DB: UPDATE events SET score, status
    
    alt Status = CONFIRMADO
        V->>MQ: Publish(confirmed_events)
        MQ->>NT: Consume confirmed
        NT->>DB: SELECT subscriptions
        NT->>TG: Send message
        NT->>DB: INSERT INTO notifications
    else Status = EN_VERIFICACION
        V->>DB: Mark for review
    end
```

### RabbitMQ Queues

1. **`raw_events`**
   - Producer: Scraper Service
   - Consumer: Normalizer Service
   - Durable: Yes
   - Contenido: Eventos crudos con `raw_payload`

2. **`normalized_events`**
   - Producer: Normalizer Service
   - Consumer: Verifier Service
   - Durable: Yes
   - Contenido: Eventos normalizados con schema común

3. **`confirmed_events`**
   - Producer: Verifier Service
   - Consumer: Notifier Service
   - Durable: Yes
   - Contenido: Eventos con score >= 70

**Acceso a RabbitMQ Management**:
- URL: `http://localhost:15672`
- Usuario: `sacv`
- Password: `rabbitmq_secure_password_2026`

---

## ⚙️ Configuración y Despliegue

### Variables de Entorno

Archivo: `.env`

```bash
# Database
DB_PASSWORD=sacv_secure_password_2026

# RabbitMQ
RABBITMQ_PASSWORD=rabbitmq_secure_password_2026

# JWT Secret
JWT_SECRET=your_jwt_secret_key_change_this_in_production

# Telegram Bot
TELEGRAM_BOT_TOKEN=8580064066:AAFzYjfvy7LYjM3RofcxReTzu3o2OqTE01c

# Email SMTP (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# Grafana (opcional)
GRAFANA_PASSWORD=admin
```

### Docker Compose

**Iniciar todos los servicios**:
```bash
docker-compose up -d
```

**Ver logs**:
```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker logs sacv_scraper -f
docker logs sacv_notifier -f
docker logs sacv_telegram_bot -f
```

**Reiniciar servicio**:
```bash
docker-compose restart scraper
docker-compose restart notifier
docker-compose restart telegram-bot
```

**Reconstruir servicio**:
```bash
docker-compose up -d --build scraper
docker-compose up -d --build telegram-bot
```

**Detener todo**:
```bash
docker-compose down
```

**Limpiar volúmenes**:
```bash
docker-compose down -v
```

### Healthchecks

Cada servicio tiene healthcheck configurado:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U sacv_user -d sacv_db"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Verificar estado**:
```bash
docker-compose ps
```

---

## 📱 Telegram Bot

### Información del Bot

- **Username**: `@AlertasComunitariasBot`
- **Token**: Configurado en `.env` como `TELEGRAM_BOT_TOKEN`

### Comandos del Usuario

1. **`/start`**
   - Muestra bienvenida y menú de provincias
   - Permite suscribirse

2. **`/suscribir`**
   - Muestra menú de provincias

3. **`/ayuda`**
   - Muestra información de ayuda

### Flujo de Suscripción

```
Usuario: /start
Bot: Muestra teclado inline con 24 provincias

Usuario: Click en "PICHINCHA"
Bot: 
  1. Desactiva suscripciones previas del usuario
  2. Inserta/actualiza suscripción a Pichincha
  3. Muestra confirmación con botones:
     - 🔄 Cambiar Provincia
     - ❌ Cancelar Alertas

Usuario: Click en "Cambiar Provincia"
Bot: Vuelve a mostrar menú de provincias

Usuario: Click en "Cancelar Alertas"
Bot: Desactiva todas las suscripciones del usuario
```

### Formato de Notificaciones

```
🚨 *ALERTA: SISMO*

📍 *Provincia:* Pichincha
📝 *Detalle:* Sismo de magnitud 4.5 detectado en Quito
📅 *Fecha:* 2026-01-30 22:00:00
```

### Debugging del Bot

**Ver logs del bot**:
```bash
docker logs sacv_telegram_bot -f
```

**Logs esperados**:
```json
{"event": "telegram_bot_starting", "timestamp": "...", "level": "info"}
{"event": "database_connected", "timestamp": "...", "level": "info"}
{"event": "bot_polling_started", "timestamp": "...", "level": "info"}
```

**Errores comunes**:

1. **Bot no responde**:
   - Verificar que el contenedor está corriendo: `docker ps | grep telegram_bot`
   - Verificar token en `.env`
   - Ver logs: `docker logs sacv_telegram_bot`

2. **Error de base de datos**:
   - Verificar que PostgreSQL está healthy
   - Verificar `DATABASE_URL` en docker-compose.yml

3. **Suscripción no se guarda**:
   - Verificar que existe al menos un usuario en tabla `users`
   - Ver logs para errores de SQL

---

## 🔍 Guía de Debugging

### Logs Estructurados

Todos los servicios usan **structlog** con formato JSON:

```json
{
  "event": "event_normalized",
  "type": "sismo",
  "zone": "Pichincha",
  "severity": "Media",
  "dedup_hash": "a1b2c3d4",
  "timestamp": "2026-01-30T22:00:00.000000Z",
  "level": "info"
}
```

### Comandos de Debugging

#### 1. Verificar Estado de Servicios

```bash
docker-compose ps
```

Todos deben mostrar "Up" o "Up (healthy)".

#### 2. Ver Logs en Tiempo Real

```bash
# Scraper
docker logs sacv_scraper -f --tail 50

# Normalizer
docker logs sacv_normalizer -f --tail 50

# Verifier
docker logs sacv_verifier -f --tail 50

# Notifier
docker logs sacv_notifier -f --tail 50

# Telegram Bot
docker logs sacv_telegram_bot -f --tail 50

# API
docker logs sacv_api -f --tail 50
```

#### 3. Conectar a PostgreSQL

```bash
docker exec -it sacv_postgres psql -U sacv_user -d sacv_db
```

**Consultas útiles**:

```sql
-- Ver fuentes activas
SELECT name, type, active, frequency_sec FROM sources;

-- Ver últimos eventos crudos
SELECT raw_id, source_id, fetched_at, raw_hash 
FROM raw_events 
ORDER BY fetched_at DESC 
LIMIT 5;

-- Ver eventos normalizados
SELECT event_id, type, zone, severity, status, score, created_at 
FROM events 
ORDER BY created_at DESC 
LIMIT 10;

-- Ver suscripciones activas
SELECT sub_id, province_id, channel_id, active 
FROM subscriptions 
WHERE active = true;

-- Ver notificaciones recientes
SELECT notif_id, event_id, channel, to_address, status, sent_at 
FROM notifications 
ORDER BY sent_at DESC 
LIMIT 10;

-- Estadísticas de eventos por status
SELECT status, COUNT(*) as total, AVG(score) as avg_score 
FROM events 
GROUP BY status;

-- Salir
\q
```

#### 4. Verificar RabbitMQ

**UI Web**: `http://localhost:15672`

**CLI**:
```bash
docker exec sacv_rabbitmq rabbitmqctl list_queues name messages
```

#### 5. Verificar Redis

```bash
docker exec -it sacv_redis redis-cli

# Comandos útiles
KEYS *
GET rate_limit:*
TTL rate_limit:some-source-id
```

#### 6. Probar API

```bash
# Health check
curl http://localhost:8000/health

# Estadísticas
curl http://localhost:8000/api/stats

# Eventos
curl http://localhost:8000/api/events?limit=5

# Fuentes
curl http://localhost:8000/api/sources
```

### Problemas Comunes

#### Problema: Servicios no inician

**Síntoma**: Contenedores en estado "Exited"

**Solución**:
```bash
# Ver logs del servicio
docker logs sacv_scraper

# Reconstruir
docker-compose build scraper
docker-compose up -d scraper
```

#### Problema: No hay eventos capturados

**Síntoma**: `total_raw_events: 0` en `/api/stats`

**Solución**:
1. Verificar que scraper está corriendo
2. Ver logs: `docker logs sacv_scraper`
3. Las fuentes pueden no tener datos nuevos
4. Verificar conectividad a internet

#### Problema: Eventos no se normalizan

**Síntoma**: `raw_events` tiene datos pero `events` está vacío

**Solución**:
1. Verificar que normalizer está corriendo
2. Ver logs: `docker logs sacv_normalizer`
3. Verificar que RabbitMQ queue `raw_events` tiene mensajes
4. Verificar que no hay errores de parsing

#### Problema: Notificaciones no se envían

**Síntoma**: Eventos CONFIRMADOS pero no llegan a Telegram

**Solución**:
1. Verificar que notifier está corriendo
2. Ver logs: `docker logs sacv_notifier`
3. Verificar que hay suscripciones activas:
   ```sql
   SELECT * FROM subscriptions WHERE active = true;
   ```
4. Verificar que el evento tiene `province_id` correcto
5. Verificar token de Telegram en `.env`

#### Problema: Bot de Telegram no responde

**Síntoma**: Comandos no funcionan

**Solución**:
1. Verificar que telegram-bot está corriendo
2. Ver logs: `docker logs sacv_telegram_bot`
3. Verificar token en `.env`
4. Reiniciar bot: `docker-compose restart telegram-bot`

#### Problema: Error de Foreign Key en notifications

**Síntoma**: `ForeignKeyViolation` al insertar notificación

**Solución**:
- El `event_id` puede no existir aún en la tabla `events`
- El código maneja esto con `psycopg2.errors.ForeignKeyViolation`
- Se registra un warning y se continúa

---

## 📝 Convenciones del Código

### Estilo Python

- **PEP 8**: Seguir guía de estilo de Python
- **Type Hints**: Usar cuando sea posible
- **Docstrings**: Formato Google style

```python
def normalize_event(self, raw_event: dict) -> Optional[dict]:
    """Normalizar evento crudo a schema común.
    
    Args:
        raw_event: Evento crudo de la queue
        
    Returns:
        Evento normalizado o None si falla
        
    Raises:
        ValidationError: Si los datos no pasan validación Pydantic
    """
    pass
```

### Logging

**Usar structlog con eventos descriptivos**:

```python
logger.info("event_normalized", 
           type=event_type,
           zone=zone,
           severity=severity,
           dedup_hash=hash[:8])

logger.error("normalization_failed",
            error=str(e),
            error_type=type(e).__name__)
```

**Niveles de log**:
- `info`: Operaciones normales
- `warning`: Situaciones recuperables (rate limit, duplicados)
- `error`: Errores que requieren atención

### Manejo de Errores

**Siempre usar try/except con logging**:

```python
try:
    result = operation()
    db_conn.commit()
except psycopg2.errors.ForeignKeyViolation:
    db_conn.rollback()
    logger.warning("foreign_key_violation", reason="...")
except Exception as e:
    db_conn.rollback()
    logger.error("operation_failed", error=str(e))
finally:
    cursor.close()
```

### Conexiones a BD

**Siempre cerrar cursores y conexiones**:

```python
cursor = db_conn.cursor()
try:
    cursor.execute("...")
    result = cursor.fetchone()
    db_conn.commit()
    return result
except Exception as e:
    db_conn.rollback()
    logger.error("query_failed", error=str(e))
    return None
finally:
    cursor.close()
```

### RabbitMQ

**Siempre hacer acknowledge**:

```python
def callback(self, ch, method, properties, body):
    try:
        event = json.loads(body)
        success = self.process_event(event)
        
        if success:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # No requeue para evitar loops infinitos
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error("callback_error", error=str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
```

### Pydantic Models

**Usar para validación de datos**:

```python
from pydantic import BaseModel, Field

class NormalizedEvent(BaseModel):
    type: str
    occurred_at: datetime
    zone: str
    severity: str
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    evidence_url: Optional[str] = None
    source_id: str
    dedup_hash: str
```

---

## 🎓 Conceptos Clave para IAs

### Event-Driven Architecture

Este proyecto usa **arquitectura orientada a eventos**:

1. **Eventos son inmutables**: `raw_events` nunca se modifican
2. **Procesamiento asíncrono**: Cada servicio procesa a su ritmo
3. **Desacoplamiento**: Servicios se comunican vía queues, no directamente
4. **Resiliencia**: Si un servicio falla, los mensajes esperan en la queue

### Deduplicación

**Dos niveles de deduplicación**:

1. **raw_events**: `raw_hash` (SHA256 del payload completo)
   - Evita capturar el mismo evento múltiples veces

2. **events**: `dedup_hash` (SHA256 de tipo + zona + fecha)
   - Evita eventos duplicados de diferentes fuentes
   - Permite actualizar eventos del mismo día

### Scoring System

**Sistema de puntuación de confianza**:

- **0-39**: NO_VERIFICADO (se descarta)
- **40-69**: EN_VERIFICACION (requiere revisión manual)
- **70-100**: CONFIRMADO (se notifica automáticamente)

**Filosofía**: Mejor no notificar que enviar falsos positivos.

### Rate Limiting

**Uso de Redis para rate limiting**:

```python
rate_key = f"rate_limit:{source_id}"
if redis_client.exists(rate_key):
    # Ya se hizo scraping recientemente
    return

# Hacer scraping
scrape()

# Setear rate limit (60 segundos)
redis_client.setex(rate_key, 60, "1")
```

**Propósito**: Evitar bloqueos de IPs por las fuentes oficiales.

### Telegram Bot Patterns

**Uso de InlineKeyboardMarkup**:

```python
keyboard = [
    [InlineKeyboardButton("Opción 1", callback_data="opt_1")],
    [InlineKeyboardButton("Opción 2", callback_data="opt_2")]
]
reply_markup = InlineKeyboardMarkup(keyboard)
```

**Callbacks**:
- Formato: `action_parameter`
- Ejemplo: `sub_17` (suscribirse a provincia 17)

### Async/Await en Telegram

**El bot usa async/await**:

```python
async def send_telegram_msg(self, chat_id, event):
    async with self.bot:
        await self.bot.send_message(
            chat_id=chat_id, 
            text=mensaje, 
            parse_mode='Markdown'
        )
```

**Importante**: Usar `asyncio.run()` o `loop.run_until_complete()` cuando se llama desde código síncrono.

---

## 📚 Recursos Adicionales

### Documentación del Proyecto

- **README.md**: Guía de instalación y uso
- **architecture_overview.md**: Diagramas detallados
- **SRS_COMPLETO_v2.md**: Especificación completa
- **PRESENTACION_DEMO.md**: Presentación del proyecto
- **KANBAN.md**: Estado del proyecto

### Scripts Útiles

**Poblar datos históricos**:
```bash
# Windows PowerShell
Get-Content scripts/populate_historical_data.sql | docker exec -i sacv_postgres psql -U sacv_user -d sacv_db

# Linux/Mac
docker exec -i sacv_postgres psql -U sacv_user -d sacv_db < scripts/populate_historical_data.sql
```

**Simular eventos**:
```bash
python scripts/simulate_events.py
```

#### Script de Simulación de Eventos

**Ubicación**: `scripts/simulate_events.py`

Este script permite enviar eventos de prueba directamente a la queue `confirmed_events` para probar el sistema de notificaciones sin esperar a que el scraper capture eventos reales.

**Características**:

1. **Menú Interactivo**: Opciones predefinidas para pruebas rápidas
2. **IDs Numéricos**: Usa los IDs correctos de provincias (1-24)
3. **Eventos Personalizados**: Permite crear eventos custom
4. **Validación**: Verifica que la provincia existe antes de enviar

**Estructura del Payload**:

```python
payload = {
    "event_id": str(uuid.uuid4()),
    "type": event_type,              # 'sismo', 'lluvia', 'corte'
    "province_id": province_id,      # ID numérico (1-24)
    "province_name": province_name,  # Nombre en MAYÚSCULAS
    "title": title,
    "description": description,
    "severity": severity,            # 'Alta', 'Media', 'Baja'
    "score": 95,                     # Score alto para asegurar CONFIRMADO
    "occurred_at": "2026-01-30T22:15:00"
}
```

**Mapeo de Provincias**:

```python
PROVINCIAS_IDS = {
    "AZUAY": 1, "BOLIVAR": 2, "CAÑAR": 3, "CARCHI": 4, "COTOPAXI": 5,
    "CHIMBORAZO": 6, "EL ORO": 7, "ESMERALDAS": 8, "GUAYAS": 9, "IMBABURA": 10,
    "LOJA": 11, "LOS RIOS": 12, "MANABI": 13, "MORONA SANTIAGO": 14, "NAPO": 15,
    "PASTAZA": 16, "PICHINCHA": 17, "TUNGURAHUA": 18, "ZAMORA CHINCHIPE": 19,
    "GALAPAGOS": 20, "SUCUMBIOS": 21, "ORELLANA": 22, "STO. DOMINGO": 23, "SANTA ELENA": 24
}
```

**Opciones del Menú**:

```
1. 🌍 Sismo en PICHINCHA (ID: 17)
2. 🌧️  Lluvia en GUAYAS (ID: 9)
3. ⚡ Corte en LOJA (ID: 11)
4. 🌍 Sismo en MANABI (ID: 13)
5. ⚡ Corte en AZUAY (ID: 1)
7. ✏️  Evento Personalizado (Manual)
0. ❌ Salir
```

**Ejemplo de Uso**:

```bash
# Ejecutar el script
python scripts/simulate_events.py

# Seleccionar opción 1 (Sismo en Pichincha)
👉 Selecciona una opción: 1

# Output esperado:
✅ [EXITO] Evento 'sismo' enviado a PICHINCHA (ID: 17)
   🆔 Event ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

⏸️  Presiona ENTER para continuar...
```

**Crear Evento Personalizado**:

```bash
# Seleccionar opción 7
👉 Selecciona una opción: 7

# Ingresar datos
👉 Tipo (sismo/lluvia/corte): sismo
👉 Provincia (MAYÚSCULAS): PICHINCHA
👉 Título: Sismo de prueba
👉 Descripción: Evento de prueba para validar notificaciones
👉 Severidad (Alta/Media/Baja): Alta
```

**Debugging**:

Si el evento no llega a Telegram:

1. Verificar que el notifier está corriendo: `docker logs sacv_notifier -f`
2. Verificar que hay suscripciones activas para esa provincia:
   ```sql
   SELECT * FROM subscriptions WHERE province_id = 17 AND active = true;
   ```
3. Verificar que RabbitMQ recibió el mensaje: http://localhost:15672
4. Ver logs del notifier para errores

**IMPORTANTE**: El script envía directamente a `confirmed_events`, saltándose el scraper, normalizer y verifier. Es ideal para pruebas rápidas del sistema de notificaciones.

### Endpoints de Desarrollo

- **API Docs**: http://localhost:8000/docs
- **RabbitMQ UI**: http://localhost:15672
- **PostgreSQL**: localhost:5432

### Credenciales por Defecto

**PostgreSQL**:
- Usuario: `sacv_user`
- Password: `sacv_secure_password_2026`
- Database: `sacv_db`

**RabbitMQ**:
- Usuario: `sacv`
- Password: `rabbitmq_secure_password_2026`

**Admin User**:
- Email: `admin@sacv.local`
- Password: `admin123`

---

## 🚀 Próximos Pasos (Roadmap)

### Funcionalidades Pendientes

1. **Admin Panel** (Frontend Vue.js)
   - Dashboard con métricas
   - Gestión de fuentes
   - Revisión manual de eventos EN_VERIFICACION

2. **Autenticación JWT**
   - Login/registro de usuarios
   - Roles (admin, operator, user)

3. **Notificaciones Email**
   - Implementar SMTP
   - Templates HTML

4. **Notificaciones WhatsApp**
   - Integración con Twilio

5. **Monitoreo**
   - Prometheus + Grafana
   - Dashboards de métricas

6. **CI/CD**
   - GitHub Actions
   - Tests automatizados

7. **Traefik**
   - Reverse proxy
   - HTTPS con Let's Encrypt

---

## 📞 Contacto y Soporte

**Autor**: Charlie Cardenas Toledo
**Institución**: UIDE - Universidad Internacional del Ecuador
**GitHub**: [@CharlieCardenasToledo](https://github.com/CharlieCardenasToledo)

---

## 🔑 Puntos Clave para IAs

### Al Asistir con este Proyecto

1. **Siempre verificar el orden de columnas** en INSERTs, especialmente en `notifications`
2. **Usar `province_id` (INTEGER)** en lugar de `zone` (VARCHAR) para suscripciones
3. **El bot usa async/await**, no olvidar `await` en funciones async
4. **Los logs son JSON estructurado**, usar `logger.info("event_name", key=value)`
5. **Deduplicación es crítica**, siempre usar `ON CONFLICT DO NOTHING/UPDATE`
6. **Rate limiting en Redis** previene bloqueos de IPs
7. **Score >= 70 = CONFIRMADO**, solo estos se notifican
8. **Cada servicio es independiente**, se comunican vía RabbitMQ
9. **Docker Compose maneja todo**, no ejecutar servicios manualmente
10. **Telegram bot y notifier son servicios separados** del mismo Dockerfile
11. **ON CONFLICT en subscriptions** ahora es solo por `channel_id`, no por `(channel_id, province_id)`
12. **Validar user_id** antes de INSERT en subscriptions (no usar subquery directamente)
13. **Debug logging**: Usar `print()` además de `logger` para facilitar debugging en Docker
14. **simulate_events.py** envía directamente a `confirmed_events` para pruebas rápidas

### Al Debuggear

1. **Empezar por los logs**: `docker logs <servicio> -f`
2. **Verificar healthchecks**: `docker-compose ps`
3. **Revisar queues en RabbitMQ**: http://localhost:15672
4. **Consultar BD directamente**: `docker exec -it sacv_postgres psql -U sacv_user -d sacv_db`
5. **Probar API**: `curl http://localhost:8000/api/stats`

### Al Modificar Código

1. **Reconstruir el servicio**: `docker-compose up -d --build <servicio>`
2. **Ver logs inmediatamente**: `docker logs <contenedor> -f`
3. **Verificar que no hay errores de sintaxis** antes de rebuild
4. **Mantener el formato de logging JSON**
5. **Actualizar este AGENTS.md** si cambias arquitectura

---

**Última actualización**: 30-ene-2026 22:38  
**Versión**: 1.0.1  
**Estado**: Completo y Validado ✅

### Cambios Recientes (v1.0.1)

- ✅ Mejorada lógica de suscripción con validación de `user_id`
- ✅ Cambiado `ON CONFLICT` de `(channel_id, province_id)` a `(channel_id)` para permitir cambio de provincia
- ✅ Añadido debug logging con `print()` statements en subscription_handler
- ✅ Actualizado `simulate_events.py` con menú interactivo y provincias correctas
- ✅ Documentación completa del script de simulación de eventos

