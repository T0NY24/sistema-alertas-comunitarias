import smtplib
import os
import logging
from email.message import EmailMessage

# Configuración de Logs
logger = logging.getLogger("EmailClient")

def enviar_correo_alerta(evento):
    """
    Envía una alerta formateada por correo electrónico.
    """
    # 1. Obtener credenciales de las variables de entorno (Docker)
    EMAIL_USER = os.getenv('GMAIL_USER')
    EMAIL_PASS = os.getenv('GMAIL_PASSWORD')
    DESTINATARIO = os.getenv('ADMIN_EMAIL')

    # Validación simple
    if not EMAIL_USER or not EMAIL_PASS:
        logger.error("❌ Faltan credenciales GMAIL_USER o GMAIL_PASSWORD en docker-compose.")
        return

    if not DESTINATARIO:
        logger.warning("⚠️ No hay ADMIN_EMAIL definido. No se enviará correo.")
        return

    try:
        # 2. Construir el mensaje
        msg = EmailMessage()
        msg['Subject'] = f"🚨 ALERTA SACV: {evento.get('title', 'Evento Detectado')}"
        msg['From'] = EMAIL_USER
        msg['To'] = DESTINATARIO

        # Cuerpo del correo en HTML para que se vea profesional
        cuerpo_html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 5px; max-width: 600px;">
                <h2 style="color: #d9534f; margin-top: 0;">⚠️ Nueva Alerta Detectada</h2>
                <p>El sistema SACV ha recibido el siguiente evento crítico:</p>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">📍 Zona:</td>
                        <td style="padding: 8px;">{evento.get('province_name', evento.get('zone', 'Desconocida'))}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">🌪️ Tipo:</td>
                        <td style="padding: 8px;">{evento.get('type', 'General').upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">📉 Severidad:</td>
                        <td style="padding: 8px; color: red;">{evento.get('severity', 'Media')}</td>
                    </tr>
                </table>

                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                
                <p style="font-weight: bold;">Descripción:</p>
                <p style="background-color: #f9f9f9; padding: 10px; border-left: 4px solid #d9534f;">
                    {evento.get('description', 'Sin descripción detallada.')}
                </p>
                
                <p style="font-size: 12px; color: #777; margin-top: 30px;">
                    Este es un mensaje automático del Sistema de Alertas Comunitarias (SACV).
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.set_content("Alerta SACV (Ver en formato HTML)", subtype='plain') # Fallback texto plano
        msg.add_alternative(cuerpo_html, subtype='html')

        # 3. Conexión SSL con Gmail (Puerto 465)
        # Importante: Quitamos los espacios de la contraseña por si acaso
        password_limpia = EMAIL_PASS.replace(" ", "")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, password_limpia)
            smtp.send_message(msg)
            
        logger.info(f"✅ [EMAIL ENVIADO] Alerta enviada a {DESTINATARIO}")

    except Exception as e:
        logger.error(f"❌ Error enviando correo: {e}")