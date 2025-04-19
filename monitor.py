import os
import json
import pyfiglet
from telethon import TelegramClient, functions, events
from telethon.tl.types import User
import asyncio
from collections import Counter
import requests
from cryptography.fernet import Fernet

class TelegramMonitor:
    def __init__(self):
        self.config_file = "telegram_monitor_config.enc"
        self.key_file = "telegram_monitor_key.key"
        self.api_id = None
        self.api_hash = None
        self.bot_token = None
        self.bot_chat_id = None
        self.monitored_users = []
        self.load_or_request_credentials()
        self.show_banner()

    def show_banner(self):
        """Muestra el banner ASCII art"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(pyfiglet.figlet_format("Telegram Monitor", font="slant"))
        print("👀 Monitoreo avanzado de Telegram")
        print("👤 Creado por @ivancastl")
        print("🔗 Grupo: t.me/+_g4DIczsuI9hOWZh")
        print("="*60 + "\n")

    def get_encryption_key(self):
        """Genera o recupera la clave de encriptación"""
        if not os.path.exists(self.key_file):
            with open(self.key_file, "wb") as f:
                f.write(Fernet.generate_key())
        with open(self.key_file, "rb") as f:
            return f.read()

    def load_or_request_credentials(self):
        """Carga o solicita las credenciales"""
        if os.path.exists(self.config_file):
            try:
                cipher_suite = Fernet(self.get_encryption_key())
                with open(self.config_file, "rb") as f:
                    encrypted_data = f.read()
                creds = json.loads(cipher_suite.decrypt(encrypted_data).decode())
                self.api_id = creds.get('api_id')
                self.api_hash = creds.get('api_hash')
                self.bot_token = creds.get('bot_token')
                self.bot_chat_id = creds.get('bot_chat_id')
                self.monitored_users = creds.get('monitored_users', [])
            except Exception as e:
                print(f"⚠️ Error cargando credenciales: {e}")
                self.request_and_save_credentials()
        else:
            self.request_and_save_credentials()

    def request_and_save_credentials(self):
        """Solicita y guarda las credenciales de forma segura"""
        self.show_banner()
        print("🔑 Configuración inicial\n")
        
        self.api_id = input("Introduce tu api_id: ").strip()
        self.api_hash = input("Introduce tu api_hash: ").strip()
        self.bot_token = input("Token de tu bot Telegram: ").strip()
        self.bot_chat_id = input("Chat ID de destino: ").strip()
        
        users_input = input("IDs de usuarios a monitorear (separados por comas): ").strip()
        self.monitored_users = [int(uid.strip()) for uid in users_input.split(",") if uid.strip().isdigit()]

        try:
            cipher_suite = Fernet(self.get_encryption_key())
            creds = {
                'api_id': self.api_id,
                'api_hash': self.api_hash,
                'bot_token': self.bot_token,
                'bot_chat_id': self.bot_chat_id,
                'monitored_users': self.monitored_users
            }
            encrypted_data = cipher_suite.encrypt(json.dumps(creds).encode())
            with open(self.config_file, "wb") as f:
                f.write(encrypted_data)
            print("\n🕵️ Configuración guardada")
        except Exception as e:
            print(f"\n🔴 Error guardando configuración: {e}")
        input("\nPresiona Enter para continuar...")

    async def setup_monitoring(self, client):
        """Configura el monitoreo en tiempo real para todos los chats"""
        @client.on(events.NewMessage())
        async def handler(event):
            if event.sender_id not in self.monitored_users:
                return

            try:
                sender = await event.get_sender()
                chat = await event.get_chat()
                
                msg_text = f"""
🔔 **Nueva actividad detectada** 🔔
👤 **Usuario:** {sender.first_name or ''} {sender.last_name or ''} 
🆔 **ID:** {sender.id}
📝 **Username:** @{sender.username if sender.username else 'N/A'}
💬 **Chat:** {chat.title if hasattr(chat, 'title') else 'Privado'} (ID: {chat.id})
📅 **Fecha:** {event.message.date}
✉️ **Mensaje:** {event.message.text or '[Contenido multimedia]'}
                """
                
                if event.message.media:
                    file_path = await event.message.download_media()
                    self.send_alert(msg_text, file_path)
                    os.remove(file_path)
                else:
                    self.send_alert(msg_text)

            except Exception as e:
                print(f"⚠️ Error procesando mensaje: {e}")

    def send_alert(self, message_text, file_path=None):
        """Envía alertas al bot configurado"""
        try:
            if file_path:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
                with open(file_path, "rb") as f:
                    files = {"document": f}
                    response = requests.post(url, data={"chat_id": self.bot_chat_id, "caption": message_text}, files=files)
            else:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                response = requests.post(url, json={"chat_id": self.bot_chat_id, "text": message_text, "parse_mode": "Markdown"})

            if response.status_code != 200:
                print(f"⚠️ Error enviando alerta: {response.text}")
        except Exception as e:
            print(f"🔴 Error en send_alert: {e}")

    async def run_monitoring(self):
        """Inicia el monitoreo en tiempo real"""
        client = TelegramClient("telegram_monitor_session", self.api_id, self.api_hash)
        await client.start()
        
        print("\n👀 **Iniciando monitoreo en tiempo real**")
        print(f"👥 Usuarios monitoreados: {len(self.monitored_users)}")
        print("⚠️ Presiona Ctrl+C para detener\n")
        
        await self.setup_monitoring(client)
        await client.run_until_disconnected()

    async def run(self):
        """Menú principal de la aplicación"""
        client = None
        try:
            client = TelegramClient("telegram_monitor_session", self.api_id, self.api_hash)
            await client.start()
            
            while True:
                self.show_banner()
                print("⚙️ Menú Principal")
                print("1 👀 Iniciar monitoreo en tiempo real")
                print("2 👥 Configurar usuarios monitoreados")
                print("3 🔑 Cambiar configuración")
                print("4 🚪 Salir\n")
                
                choice = input("🚩 Selecciona una opción: ").strip()
                
                if choice == "1":
                    await self.run_monitoring()
                    break
                elif choice == "2":
                    await self.configure_monitored_users()
                elif choice == "3":
                    os.remove(self.config_file) if os.path.exists(self.config_file) else None
                    self.request_and_save_credentials()
                    return
                elif choice == "4":
                    print("\n👋 ¡Hasta pronto!")
                    break
                else:
                    print("\n⚠️ Opción no válida")
                
                input("\nPresiona Enter para continuar...")
                
        finally:
            if client:
                await client.disconnect()

    async def configure_monitored_users(self):
        """Permite configurar los usuarios a monitorear"""
        self.show_banner()
        print("👥 Configurar usuarios monitoreados\n")
        
        current_users = ", ".join(map(str, self.monitored_users)) if self.monitored_users else "Ninguno"
        print(f"Usuarios actuales: {current_users}")
        
        users_input = input("\nIngresa nuevos IDs a monitorear (separados por comas): ").strip()
        new_users = [int(uid.strip()) for uid in users_input.split(",") if uid.strip().isdigit()]
        
        if new_users:
            self.monitored_users = new_users
            try:
                cipher_suite = Fernet(self.get_encryption_key())
                with open(self.config_file, "rb") as f:
                    encrypted_data = f.read()
                creds = json.loads(cipher_suite.decrypt(encrypted_data).decode())
                creds['monitored_users'] = self.monitored_users
                encrypted_data = cipher_suite.encrypt(json.dumps(creds).encode())
                with open(self.config_file, "wb") as f:
                    f.write(encrypted_data)
                print("\n🕵️ Usuarios actualizados")
            except Exception as e:
                print(f"\n🔴 Error actualizando usuarios: {e}")
        else:
            print("\n⚠️ No se ingresaron IDs válidos")

        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    try:
        monitor = TelegramMonitor()
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n🛑 Monitoreo detenido")
    except Exception as e:
        print(f"\n🔴 Error crítico: {e}")