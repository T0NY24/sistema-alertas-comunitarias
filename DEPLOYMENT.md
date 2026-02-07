# Guía de Despliegue en Railway

Esta guía te ayudará a desplegar el **Sistema de Alertas Comunitarias** en Railway.app de manera rápida y sencilla.

## ¿Por qué Railway?

Railway es perfecto para este proyecto porque:
- ✅ Soporta Docker Compose nativamente
- ✅ Provee PostgreSQL y Redis managed gratis
- ✅ Permite servicios que corren continuamente (scrapers, bots)
- ✅ Configuración simple en minutos
- ✅ Plan gratuito generoso ($5 USD de crédito mensual)

## Prerequisitos

1. **Cuenta de GitHub** con el repositorio del proyecto
2. **Cuenta de Railway** (gratis en [railway.app](https://railway.app))

## Paso 1: Preparar el Repositorio

### 1.1 Push a GitHub (si no está ya)

```bash
cd sistema-alertas-comunitarias

# Inicializar git si no existe
git init

# Agregar remote
git remote add origin https://github.com/TU_USUARIO/sistema-alertas-comunitarias.git

# Commit y push
git add .
git commit -m "Preparar para despliegue en Railway"
git push -u origin main
```

### 1.2 Verificar que `.env` NO esté en el repositorio

El archivo `.env` debe estar en `.gitignore`. Verificar:

```bash
cat .gitignore | grep .env
```

Debe aparecer `.env` listado.

## Paso 2: Crear Proyecto en Railway

### 2.1 Acceder a Railway

1. Ve a [railway.app](https://railway.app)
2. Click en **"Login"** → Inicia sesión con GitHub
3. Autoriza a Railway para acceder a tus repositorios

### 2.2 Crear Nuevo Proyecto

1. Click en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Busca y selecciona `sistema-alertas-comunitarias`
4. Railway detectará automáticamente `docker-compose.yml`

### 2.3 Railway Desplegará Automáticamente

Railway creará un servicio por cada contenedor en `docker-compose.yml`:
- `postgres`
- `redis`
- `rabbitmq`
- `scraper`
- `normalizer`
- `verifier`
- `notifier`
- `telegram-bot`
- `api-gateway`
- `admin-panel`

⏳ **Espera 5-10 minutos** mientras Railway construye e inicia todos los servicios.

## Paso 3: Configurar Variables de Entorno

### 3.1 Acceder a Variables de Entorno

En el dashboard de Railway:
1. Click en cada servicio
2. Ve a la pestaña **"Variables"**

### 3.2 Configurar Variables Globales

Railway permite variables compartidas. Click en **"Shared Variables"** y añade:

```bash
DB_PASSWORD=tu_password_seguro_aqui
RABBITMQ_PASSWORD=tu_rabbitmq_password_aqui
JWT_SECRET=tu_jwt_secret_aqui
TELEGRAM_BOT_TOKEN=8580064066:AAFzYjfvy7LYjM3RofcxReTzu3o2OqTE01c
GMAIL_USER=ap761324@gmail.com
GMAIL_PASSWORD=fcfb voll gebo zwap
ADMIN_EMAIL=ap761324@gmail.com
```

> [!IMPORTANT]
> Cambia las contraseñas por valores seguros en producción

### 3.3 Railway Provee PostgreSQL y Redis Managed

Railway puede proveer bases de datos managed. Para usarlas:

1. Click en **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Click en **"+ New"** → **"Database"** → **"Add Redis"**
3. Railway generará automáticamente las variables:
   - `DATABASE_URL`
   - `REDIS_URL`

Estas reemplazarán las URLs de los contenedores locales.

### 3.4 Actualizar docker-compose.yml para Railway (Opcional)

Si usas bases de datos managed de Railway, puedes comentar los servicios de postgres y redis en `docker-compose.yml`.

## Paso 4: Configurar Dominios Públicos

### 4.1 Exponer API Gateway

1. Click en el servicio **`api-gateway`**
2. Ve a **"Settings"** → **"Networking"**
3. Click en **"Generate Domain"**
4. Railway generará una URL como: `https://sacv-api.up.railway.app`

### 4.2 Exponer Admin Panel

1. Click en el servicio **`admin-panel`**
2. Ve a **"Settings"** → **"Networking"**
3. Click en **"Generate Domain"**
4. Railway generará una URL como: `https://sacv-admin.up.railway.app`

### 4.3 Actualizar Variables de Entorno del Frontend

1. Click en servicio **`admin-panel`**
2. En **"Variables"**, añade:
   ```
   VITE_API_URL=https://sacv-api.up.railway.app
   ```
3. Re-deploy el servicio

## Paso 5: Verificar el Despliegue

### 5.1 Health Check de la API

```bash
curl https://sacv-api.up.railway.app/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2026-02-06T22:00:00.000000"
}
```

### 5.2 Verificar Admin Panel

Abre en tu navegador:
```
https://sacv-admin.up.railway.app
```

Deberías ver el panel de administración cargando datos de la API.

### 5.3 Verificar Logs

En Railway dashboard:
1. Click en cada servicio
2. Ve a **"Logs"** para ver la actividad

Busca mensajes como:
```json
{"event": "scraper_service_starting", "level": "info"}
{"event": "sources_loaded", "count": 3, "level": "info"}
```

### 5.4 Verificar RabbitMQ

1. Click en servicio **`rabbitmq`**
2. Genera dominio público
3. Accede a `https://tu-rabbitmq.up.railway.app:15672`
4. Login: `sacv` / tu contraseña de RabbitMQ

## Paso 6: Poblar Base de Datos (Opcional)

Conectar a PostgreSQL en Railway y ejecutar scripts:

```bash
# Obtener DATABASE_URL de Railway
# Dashboard → postgres service → Connect → Copy DATABASE_URL

# Ejecutar script de población
psql "postgresql://user:pass@host:port/dbname" < scripts/populate_historical_data.sql
```

O desde Railway CLI:

```bash
railway run psql < scripts/populate_historical_data.sql
```

## Paso 7: Configurar Dominios Personalizados (Opcional)

### 7.1 Agregar Dominio Propio

Si tienes un dominio:
1. En Railway, servicio `admin-panel` → **"Settings"** → **"Domains"**
2. Click **"Custom Domain"**
3. Ingresa tu dominio (ej: `alertas.tudominio.com`)
4. Railway te dará registros DNS para configurar

### 7.2 Configurar DNS

En tu proveedor de dominio (GoDaddy, Namecheap, etc.):
```
Type: CNAME
Name: alertas
Value: [URL generada por Railway]
```

## Troubleshooting

### Servicios no inician

**Síntoma:** Servicios en estado "Crashed"

**Solución:**
1. Revisar logs del servicio
2. Verificar que todas las variables de entorno estén configuradas
3. Verificar que las dependencias (postgres, rabbitmq) estén healthy

### Error de conexión a base de datos

**Síntoma:** `could not connect to server`

**Solución:**
1. Verificar que `DATABASE_URL` esté correctamente configurada
2. Verificar que el servicio PostgreSQL esté running
3. Verificar network connectivity entre servicios

### Admin Panel no carga datos

**Síntoma:** Frontend carga pero sin datos

**Solución:**
1. Verificar que `VITE_API_URL` apunte a la URL correcta
2. Verificar CORS en API Gateway (debe permitir dominio de Railway)
3. Re-deploy el servicio `admin-panel` después de cambiar variables

### Rate Limits / Costos

Railway ofrece $5 USD de crédito mensual gratis. Si excedes:
- Optimiza servicios (reducir replicas)
- Usa sleep mode para servicios no críticos
- Considera plan de pago ($5/mes por usuario)

## URLs Importantes

Una vez desplegado, anota estas URLs:

- **Admin Panel:** `https://sacv-admin.up.railway.app`
- **API Gateway:** `https://sacv-api.up.railway.app`
- **Swagger Docs:** `https://sacv-api.up.railway.app/docs`
- **RabbitMQ UI:** `https://sacv-rabbitmq.up.railway.app:15672`

## Monitoreo

Railway provee:
- **Metrics:** CPU, RAM, Network por servicio
- **Logs:** Logs en tiempo real
- **Alerts:** Configurar alertas por email

## Costos Estimados

**Plan Gratuito:**
- $5 USD de crédito mensual
- Suficiente para MVP/demo

**Plan Pro:**
- $20/mes
- Para producción con tráfico moderado

**Optimizaciones:**
- Usar PostgreSQL/Redis managed de Railway (evita contenedores extra)
- Consolidar servicios pequeños si es posible
- Implementar sleep mode en horarios de baja demanda

## Soporte

- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Discord:** [Railway Community](https://discord.gg/railway)
- **GitHub:** [Issues del proyecto]

---

**¡Listo!** Tu sistema debería estar funcionando en Railway 🚀
