"""
Telegram Bot Handler - Sistema de Alertas Comunitarias Verificadas
Maneja comandos del bot y suscripciones de usuarios
"""
import os
import asyncio
import psycopg2
import structlog
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from subscription_handler import mostrar_menu_provincias, manejar_callback_suscripcion

# Configuración de Logs
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Configuración de Entorno
DATABASE_URL = os.getenv('DATABASE_URL')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def main():
    """Inicialización del Bot con patrón asíncrono correcto para v20.7"""
    logger.info("telegram_bot_starting")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("telegram_token_missing")
        return

    # 1. Conexión a la base de datos
    try:
        conn = psycopg2.connect(DATABASE_URL)
        logger.info("database_connected")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return

    # 2. Configuración de la Aplicación (v20.7)
    builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    application = builder.build()

    # 3. Registro de Handlers
    application.add_handler(CommandHandler("start", mostrar_menu_provincias))
    application.add_handler(CommandHandler("suscribir", mostrar_menu_provincias))
    
    # El patrón ".*" captura todas las interacciones de botones (sub_, ir_menu, cancelar_todo)
    application.add_handler(
        CallbackQueryHandler(
            lambda u, c: manejar_callback_suscripcion(u, c, conn),
            pattern=".*"
        )
    )

    # 4. Ejecución asíncrona compatible con Docker
    async with application:
        await application.initialize()
        await application.start()
        logger.info("telegram_bot_ready")
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Mantiene el servicio activo sin bloquear el loop
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("telegram_bot_stopping")
            await application.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical("bot_crashed", error=str(e))
