"""
Subscription Handler - Manejo de suscripciones del bot de Telegram
Centraliza la lógica del menú de provincias y actualización de suscripciones
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import uuid
import logging

logger = logging.getLogger(__name__)


def crear_teclado_provincias():
    """Genera el teclado dinámico para /start y /suscribir"""
    provincias = [
        "AZUAY", "BOLIVAR", "CAÑAR", "CARCHI", "CHIMBORAZO", 
        "COTOPAXI", "EL ORO", "ESMERALDAS", "GUAYAS", "IMBABURA", 
        "LOJA", "LOS RIOS", "MANABI", "PICHINCHA", "SANTA ELENA", 
        "TUNGURAHUA"
    ]
    keyboard = []
    for i in range(0, len(provincias), 2):
        row = [InlineKeyboardButton(provincias[i], callback_data=f"sub_{provincias[i]}")]
        if i + 1 < len(provincias):
            row.append(InlineKeyboardButton(provincias[i+1], callback_data=f"sub_{provincias[i+1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


async def mostrar_menu_provincias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de provincias (usado por /start y /suscribir)"""
    await update.message.reply_text(
        "👋 *¡Bienvenido al SACV!*\n"
        "🚨 *Sistema de Alertas Comunitarias Verificadas*\n\n"
        "📍 *¿Qué provincia te interesa monitorear?*\n"
        "Selecciona una de las opciones de abajo.\n\n"
        "⚠️ Solo puedes tener una suscripción activa.",
        reply_markup=crear_teclado_provincias(),
        parse_mode='Markdown'
    )


async def manejar_callback_suscripcion(update: Update, context: ContextTypes.DEFAULT_TYPE, db_conn):
    """Maneja TODAS las interacciones de botones (Suscripción, Cambiar, Cancelar)"""
    query = update.callback_query
    data = query.data
    chat_id = str(query.message.chat_id)
    await query.answer()

    if data.startswith("sub_"):
        zona = data.split("_")[1]
        cursor = db_conn.cursor()
        try:
            # Lógica de 'una sola ciudad': desactivar previas y hacer Upsert
            cursor.execute("UPDATE subscriptions SET active = false WHERE channel_id = %s", (chat_id,))
            cursor.execute("""
                INSERT INTO subscriptions (sub_id, user_id, zone, channel_id, active, channel, type)
                VALUES (%s, (SELECT user_id FROM users LIMIT 1), %s, %s, true, 'telegram', NULL)
                ON CONFLICT (channel_id) DO UPDATE SET zone = EXCLUDED.zone, active = true, type = NULL;
            """, (str(uuid.uuid4()), zona, chat_id))
            db_conn.commit()

            # Menú de gestión tras éxito
            keyboard = [
                [InlineKeyboardButton("🔄 Cambiar Provincia", callback_data="ir_menu")],
                [InlineKeyboardButton("❌ Cancelar Alertas", callback_data="cancelar_todo")]
            ]
            await query.edit_message_text(
                text=f"✅ *Suscripción Guardada*\n\nRecibirás alertas de: `{zona}`\n\n"
                     f"Puedes cambiar tu provincia o cancelar en cualquier momento.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            logger.info(f"Suscripción actualizada para chat_id {chat_id} a zona {zona}")
            
        except Exception as e:
            db_conn.rollback()
            logger.error(f"Error al guardar suscripción: {e}")
            await query.edit_message_text("❌ Error al guardar en base de datos.")
        finally:
            cursor.close()

    elif data == "ir_menu":
        await query.edit_message_text(
            "📍 *Cambiar Provincia*\n\nSelecciona tu nueva provincia:", 
            reply_markup=crear_teclado_provincias(),
            parse_mode='Markdown'
        )

    elif data == "cancelar_todo":
        cursor = db_conn.cursor()
        try:
            cursor.execute("UPDATE subscriptions SET active = false WHERE channel_id = %s", (chat_id,))
            db_conn.commit()
            logger.info(f"Suscripción cancelada para chat_id {chat_id}")
            await query.edit_message_text(
                "🚫 *Alertas Desactivadas*\n\n"
                "Ya no recibirás notificaciones.\n\n"
                "Usa /suscribir para volver a activarlas.",
                parse_mode='Markdown'
            )
        except Exception as e:
            db_conn.rollback()
            logger.error(f"Error al cancelar suscripción: {e}")
            await query.edit_message_text("❌ Error al cancelar alertas.")
        finally:
            cursor.close()
