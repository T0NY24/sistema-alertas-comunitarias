# Quick Start - Despliegue en Railway

Esta es una guía rápida. Para instrucciones detalladas ver [DEPLOYMENT.md](./DEPLOYMENT.md)

## 1. Push a GitHub

```bash
git add .
git commit -m "Preparar para despliegue Railway"
git push origin main
```

## 2. Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app) y login con GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Selecciona `sistema-alertas-comunitarias`
4. Railway desplegará automáticamente todos los servicios

## 3. Configurar Variables de Entorno

En Railway dashboard, añade estas variables compartidas:

```bash
DB_PASSWORD=tu_password_seguro
RABBITMQ_PASSWORD=tu_rabbitmq_password
JWT_SECRET=tu_jwt_secret
TELEGRAM_BOT_TOKEN=8580064066:AAFzYjfvy7LYjM3RofcxReTzu3o2OqTE01c
GMAIL_USER=ap761324@gmail.com
GMAIL_PASSWORD=fcfb voll gebo zwap
ADMIN_EMAIL=ap761324@gmail.com
```

## 4. Generar Dominios Públicos

Para `api-gateway`:
- Settings → Networking → Generate Domain
- Obtendrás: `https://tu-api.up.railway.app`

Para `admin-panel`:
- Settings → Networking → Generate Domain
- Obtendrás: `https://tu-admin.up.railway.app`

## 5. Configurar API URL en Frontend

En servicio `admin-panel`:
- Variables → Añadir:
  ```
  VITE_API_URL=https://tu-api.up.railway.app
  ```
- Re-deploy el servicio

## 6. Verificar

```bash
curl https://tu-api.up.railway.app/health
```

Abrir en navegador:
```
https://tu-admin.up.railway.app
```

**¡Listo! 🚀**

Para troubleshooting y configuración avanzada, ver [DEPLOYMENT.md](./DEPLOYMENT.md)
