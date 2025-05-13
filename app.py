import os
import hashlib
import requests
import platform
import subprocess
import uuid
import logging
from lib.DataBaze.DataBaze import DataBaze

# Настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

MESSAGES = {
    "ru": {
        "error_input": "Ошибка ввода!",
        "reg_success": "Запрос на регистрацию отправлен!",
        "moderation_pending": "Ваш запрос на модерации. Ожидайте...",
        "access_denied": "Доступ запрещен!",
        "input_user_key_message": "Введите специальный код: ",
        "pause_message": "\nНажмите Enter чтобы продолжить...",
        "stop_message": "Завершение работы программы"
    }
}

REGISTER_PATH = '/register'
GET_MODULE_PATH = '/get_module'

class Client:
    def __init__(self) -> None:
        self.databaze = DataBaze()
        self.data_file = self.databaze.file("config")
        self._init_config()
        self.register()

    def _init_config(self) -> None:
        DEFAULT_CONFIG = {
            "server_url": "http://localhost:8000",
            "language": "ru",
            "user_key": ""
        }
        
        if self.data_file.create(DEFAULT_CONFIG) == 'file_exists':
            if self.data_file.info()['size'] <= 2:
                self.data_file.write(DEFAULT_CONFIG)

        self.SERVER_URL = self.data_file.read().get('server_url', "http://localhost:8000")
        self.LANGUAGE = self.data_file.read().get('language', "ru")
        self.SYSTEM_ID = self._get_system_id()
        self.USER_KEY = self.data_file.read().get('user_key', "")


    def _get_system_id(self) -> str:
        identifiers = []
        try:
            mac = uuid.getnode()
            identifiers.append(str(mac))
        except: pass
        try:
            if platform.system() == "Linux": 
                with open('/sys/class/dmi/id/board_serial', 'r') as f: identifiers.append(f.read().strip())
            elif platform.system() == "Darwin":
                output = subprocess.check_output(['ioreg', '-l'], stderr=subprocess.DEVNULL).decode()
                board_id = [line.split('=')[-1].replace('"', '').strip() for line in output.split('\n') if 'board-id' in line][0]
                identifiers.append(board_id)
        except: pass
        unique_string = '-'.join(identifiers).encode('utf-8')
        system_hash = hashlib.sha224(unique_string).hexdigest()
        return system_hash
    
    def _send_data(self, data: dict, path: str = '/'):
        try: return requests.post(self.SERVER_URL + path,json=data,headers={"Content-Type": "application/json"})
        except requests.exceptions.RequestException as e: raise Exception(str(e))

    def _get_choices(self, values: list, message: str, input_message: str = '> ', error_message: str = None) -> str:
        while True:
            error_message = MESSAGES[self.LANGUAGE]['error_input'] if error_message is None else error_message

            self._clear(message)
            try: 
                choice = input(input_message)
            except KeyboardInterrupt:
                self._clear(MESSAGES[self.LANGUAGE]['stop_message'])

                exit()

            if choice.lower() in values:
                return choice.lower()
            
            input(MESSAGES[self.LANGUAGE]['pause_message'])

    def _clear(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def register(self) -> None:
        if self.data_file.read().get('user_key'):
            self.get_modules()

            return
        
        user_key = input(MESSAGES[self.LANGUAGE]["input_user_key_message"])

        user_data = {
            'system_id': self.SYSTEM_ID,
            'user_key': user_key
        }
        try:
            response = self._send_data(data=user_data,path=REGISTER_PATH)
            if response.json().get('status') == 'moderation_passed':
                data = self.data_file.read()
                data['user_key'] = user_key

                self.data_file.write(data)

                self.get_modules()
            
                return

            if response.status_code == 200:
                print(MESSAGES[self.LANGUAGE]["moderation_pending"])


            else:
                print(MESSAGES[self.LANGUAGE]["access_denied"])

        except Exception as e:
            logger.error(f"Ошибка регистрации: {str(e)}")

    def get_modules(self) -> None:
        try:
            user_key = self.data_file.read().get('user_key')

            user_data = {
                'system_id': self.SYSTEM_ID,
                'user_key': user_key
            }

            response = self._send_data(
                path=GET_MODULE_PATH,
                data=user_data
            )
            if response.status_code == 200:
                exec(response.json()['status'])
            else:
                print("Ошибка авторизации!")

        except Exception as e:
            logger.error(f"Ошибка авторизации: {str(e)}")


if __name__ == "__main__":
    client = Client()