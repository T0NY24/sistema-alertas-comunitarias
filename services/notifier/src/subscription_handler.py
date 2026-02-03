from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import uuid
import logging

logger = logging.getLogger(__name__)

# Diccionario oficial alineado con tus IDs de la base de datos
PROVINCIAS = {
    "1": "AZUAY", "2": "BOLIVAR", "3": "CAÑAR", "4": "CARCHI", "5": "COTOPAXI",
    "6": "CHIMBORAZO", "7": "EL ORO", "8": "ESMERALDAS", "9": "GUAYAS", "10": "IMBABURA",
    "11": "LOJA", "12": "LOS RIOS", "13": "MANABI", "14": "MORONA SANTIAGO", "15": "NAPO",
    "16": "PASTAZA", "17": "PICHINCHA", "18": "TUNGURAHUA", "19": "ZAMORA CHINCHIPE",
    "20": "GALAPAGOS", "21": "SUCUMBIOS", "22": "ORELLANA", "23": "STO. DOMINGO", "24": "SANTA ELENA"
}

def crear_teclado_provincias():
    """Genera el teclado usando IDs numéricos en el callback_data"""
    keyboard = []
    ids = list(PROVINCIAS.keys())
    # Ordenamos numéricamente para que aparezcan en orden
    ids.sort(key=int)
    
    for i in range(0, len(ids), 2):
        row = [InlineKeyboardButton(PROVINCIAS[ids[i]], callback_data=f"sub_{ids[i]}")]
        if i + 1 < len(ids):
            row.append(InlineKeyboardButton(PROVINCIAS[ids[i+1]], callback_data=f"sub_{ids[i+1]}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def mostrar_menu_provincias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de provincias corregido"""
    await update.message.reply_text(
        "👋 *¡Bienvenido al SACV!*\n"
        "🚨 *Sistema de Alertas Comunitarias Verificadas*\n\n"
        "📍 *¿Qué provincia te interesa monitorear?*\n"
        "Selecciona una opción de la lista oficial de Ecuador.",
        reply_markup=crear_teclado_provincias(),
        parse_mode='Markdown'
    )

async def manejar_callback_suscripcion(update: Update, context: ContextTypes.DEFAULT_TYPE, db_conn):
    """Maneja la suscripción usando province_id para evitar el error de NULL"""
    query = update.callback_query
    data = query.data
    chat_id = str(query.message.chat_id)
    await query.answer()

    if data.startswith("sub_"):
        # Extraemos el ID numérico (ej: "17")
        prov_id = data.split("_")[1]
        nombre_provincia = PROVINCIAS.get(prov_id, "Desconocida")
        
        cursor = db_conn.cursor()
        try:
            # 1. Obtener dinámicamente el primer usuario que encuentre (Anthony)
            cursor.execute("SELECT user_id FROM users LIMIT 1")
            row = cursor.fetchone()
            if not row:
                await query.edit_message_text("❌ Error: No hay usuarios en la tabla 'users'.")
                return
            user_id = row[0]
            
            # 2. UPSERT: Inserta o actualiza según el channel_id
            cursor.execute("""
                INSERT INTO subscriptions (sub_id, user_id, province_id, channel_id, active, channel)
                VALUES (%s, %s, %s, %s, true, 'telegram')
                ON CONFLICT (channel_id) 
                DO UPDATE SET 
                    province_id = EXCLUDED.province_id,
                    active = true;
            """, (str(uuid.uuid4()), user_id, int(prov_id), chat_id))
            
            db_conn.commit()

            keyboard = [
                [InlineKeyboardButton("🔄 Cambiar Provincia", callback_data="ir_menu")],
                [InlineKeyboardButton("❌ Cancelar Alertas", callback_data="cancelar_todo")]
            ]
            await query.edit_message_text(
                text=f"✅ *Suscripción Guardada*\n\nProvincia: `{nombre_provincia}` (ID: {prov_id})\n\n"
                     f"Recibirás alertas automáticas para esta zona.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            logger.info(f"Suscripción exitosa: Chat {chat_id} -> Provincia {prov_id}")
            print(f"✅ DEBUG: Suscripción guardada - Chat: {chat_id}, Provincia: {prov_id}")
            
        except Exception as e:
            db_conn.rollback()
            logger.error(f"Error crítico en DB: {e}")
            print(f"❌ DEBUG_ERROR: {e}")  # Esto imprimirá el error real en Docker logs
            await query.edit_message_text(f"❌ Error al guardar en base de datos.\nDetalle: {str(e)[:50]}...")
        finally:
            cursor.close()

    elif data == "ir_menu":
        await query.edit_message_text(
            "📍 *Cambiar Provincia*\n\nSelecciona tu nueva provincia:", 
            reply_markup=crear_teclado_provincias(),
            parse_mode='Markdown'
        )

    elif data == "cancelar_todo":
        # ... (Tu lógica de cancelar se mantiene igual, ya funciona con channel_id)
        cursor = db_conn.cursor()
        try:
            cursor.execute("UPDATE subscriptions SET active = false WHERE channel_id = %s", (chat_id,))
            db_conn.commit()
            await query.edit_message_text("🚫 *Alertas Desactivadas*")
        finally:
            cursor.close()