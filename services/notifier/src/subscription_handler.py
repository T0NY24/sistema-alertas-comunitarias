from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import uuid
import logging

logger = logging.getLogger(__name__)

# Diccionario oficial alineado con los IDs exactos de la base de datos
# Estos IDs deben coincidir EXACTAMENTE con la tabla provinces
PROVINCIAS = {
    "1": "Azuay",
    "2": "Bolívar",
    "3": "Cañar",
    "4": "Carchi",
    "5": "Chimborazo",
    "6": "Cotopaxi",
    "7": "El Oro",
    "8": "Esmeraldas",
    "9": "Galápagos",
    "10": "Guayas",
    "11": "Imbabura",
    "12": "Loja",
    "13": "Los Ríos",
    "14": "Manabí",
    "15": "Morona Santiago",
    "16": "Napo",
    "17": "Orellana",
    "18": "Pastaza",
    "19": "Pichincha",
    "20": "Santa Elena",
    "21": "Santo Domingo de los Tsáchilas",
    "22": "Sucumbíos",
    "23": "Tungurahua",
    "24": "Zamora Chinchipe"
}

# ID especial para alertas nacionales
ID_NACIONAL = "0"

async def mostrar_bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    👋 Pantalla de inicio amigable.
    Explica qué hace el bot y da opciones claras (Iniciar / Salir).
    """
    user_name = update.effective_user.first_name
    
    mensaje = (
        f"👋 **¡Hola {user_name}!**\n\n"
        "Bienvenido al **Sistema de Alertas Comunitarias (SACV)**. 🇪🇨\n"
        "Te notificaré sobre eventos importantes como sismos, lluvias fuertes o cortes de luz.\n\n"
        "👇 **¿Qué deseas hacer?**"
    )

    teclado = [
        [InlineKeyboardButton("🚀 Configurar mis Alertas", callback_data='ver_provincias')],
        [InlineKeyboardButton("❌ Salir / Cancelar", callback_data='salir')]
    ]
    
    reply_markup = InlineKeyboardMarkup(teclado)

    if update.message:
        await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        # Si venimos de un callback (botón "Atrás" por ejemplo)
        await update.callback_query.edit_message_text(mensaje, reply_markup=reply_markup, parse_mode='Markdown')

def crear_teclado_provincias():
    """Genera el teclado usando IDs numéricos en el callback_data e incluye Opción Nacional"""
    keyboard = []
    
    # 🌟 OPCIÓN PREMIUM: Alertas Nacionales Críticas (ID 0)
    keyboard.append([InlineKeyboardButton("🇪🇨 TODO ECUADOR (Solo Emergencias)", callback_data='sub_0')])
    
    ids = list(PROVINCIAS.keys())
    # Ordenamos numéricamente para que aparezcan en orden
    ids.sort(key=int)
    
    for i in range(0, len(ids), 2):
        row = [InlineKeyboardButton(f"📍 {PROVINCIAS[ids[i]]}", callback_data=f"sub_{ids[i]}")]
        if i + 1 < len(ids):
            row.append(InlineKeyboardButton(f"📍 {PROVINCIAS[ids[i+1]]}", callback_data=f"sub_{ids[i+1]}"))
        keyboard.append(row)
    
    # Botón de volver
    keyboard.append([InlineKeyboardButton("🔙 Volver al Inicio", callback_data='inicio')])
    
    return InlineKeyboardMarkup(keyboard)

async def mostrar_menu_provincias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de provincias corregido"""
    # Si viene de comando (no debería con nueva lógica, pero por seguridad)
    if update.message:
         await update.message.reply_text(
            "🗺️ **Selecciona tu ubicación:**\n\n"
            "Si eliges **Todo Ecuador**, solo te avisaremos de eventos de severidad **ALTA** o **MEDIA** a nivel nacional.",
            reply_markup=crear_teclado_provincias(),
            parse_mode='Markdown'
        )
         return

    query = update.callback_query
    await query.answer() # Acknowledge
    
    await query.edit_message_text(
        "🗺️ **Selecciona tu ubicación:**\n\n"
        "Si eliges **Todo Ecuador**, solo te avisaremos de eventos de severidad **ALTA** o **MEDIA** a nivel nacional.",
        reply_markup=crear_teclado_provincias(),
        parse_mode='Markdown'
    )

async def manejar_callback_suscripcion(update: Update, context: ContextTypes.DEFAULT_TYPE, db_conn):
    """Maneja todos los clics de los botones."""
    query = update.callback_query
    data = query.data
    chat_id = str(query.message.chat_id)

    if data == 'ver_provincias':
        await mostrar_menu_provincias(update, context)
    
    elif data == 'inicio':
        await mostrar_bienvenida(update, context)

    elif data == 'salir':
        await query.answer("¡Hasta pronto!")
        await query.edit_message_text("👋 ¡Gracias por visitarnos! Escribe /start cuando quieras volver.")
    
    elif data.startswith("sub_"):
        await query.answer()
        # Extraemos el ID numérico (ej: "17" o "0")
        prov_id = data.split("_")[1]
        
        nombre_provincia = "TODO ECUADOR (Alertas Críticas)" if prov_id == "0" else PROVINCIAS.get(prov_id, "Desconocida")
        
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
                [InlineKeyboardButton("🔄 Cambiar Provincia", callback_data="ver_provincias")],
                [InlineKeyboardButton("❌ Cancelar Alertas", callback_data="cancelar_todo")],
                [InlineKeyboardButton("🚪 Salir", callback_data="salir")]
            ]
            
            await query.edit_message_text(
                text=f"✅ *Suscripción Guardada*\n\nProvincia: `{nombre_provincia}` (ID: {prov_id})\n\n"
                     f"Recibirás alertas automáticas para esta zona."
                     f"{' (Solo Alta/Media)' if prov_id == '0' else ''}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            logger.info(f"Suscripción exitosa: Chat {chat_id} -> Provincia {prov_id}")
            
        except Exception as e:
            db_conn.rollback()
            logger.error(f"Error crítico en DB: {e}")
            await query.edit_message_text(f"❌ Error al guardar en base de datos.\nDetalle: {str(e)[:50]}...")
        finally:
            cursor.close()

    elif data == "ir_menu":
        # Compatibilidad hacia atrás o alias
        await mostrar_menu_provincias(update, context)

    elif data == "cancelar_todo":
        cursor = db_conn.cursor()
        try:
            cursor.execute("UPDATE subscriptions SET active = false WHERE channel_id = %s", (chat_id,))
            db_conn.commit()
            
            teclado_volver = [[InlineKeyboardButton("🔙 Volver al Inicio", callback_data='inicio')]]
            await query.edit_message_text("🚫 *Alertas Desactivadas*", reply_markup=InlineKeyboardMarkup(teclado_volver), parse_mode='Markdown')
        finally:
            cursor.close()