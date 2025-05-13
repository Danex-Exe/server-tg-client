import importlib.util
import logging
import threading
import hashlib
import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from fastapi import FastAPI, status, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import uvicorn
from dateutil.relativedelta import relativedelta

# Инициализация базы данных и конфигурации
from lib.DataBaze.DataBaze import DataBaze
DATABAZE = DataBaze(path="data/")
CONFIG_FILE = DATABAZE.file(name='config', type="json")

# Настройка логов
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# Инициализация конфига
DEFAULT_CONFIG = {
    "bot": {
        "token": "",
        "bot_admins": [],
        "server_url": "http://localhost:8000",
        "public_key": "server_public.pem",
        "modules_path": "secure_modules"
    },
    "users": {}
}

CONFIG_FILE_CREATE_RESULT = CONFIG_FILE.create(DEFAULT_CONFIG)
if CONFIG_FILE_CREATE_RESULT == 'file_exists' and CONFIG_FILE.info()['size'] <= 2:
    CONFIG_FILE.write(DEFAULT_CONFIG)

config = CONFIG_FILE.read()
TOKEN = config.get('bot', {}).get('token')
BOT_ADMINS = config.get('bot', {}).get('bot_admins', [])
SERVER_URL = config.get('bot', {}).get('server_url')

app = FastAPI()
application = Application.builder().token(TOKEN).build()

# Модели данных
class ModerationRequest(BaseModel):
    user_id: str
    client_hash: str
    encrypted_data: bytes
    signature: bytes

class RegisterRequest(BaseModel):
    system_id: str
    user_key: str


import time
from datetime import datetime, timedelta
import time
from datetime import datetime, timedelta

class TimeUtils:
    def __init__(self):
        pass

    @staticmethod
    def current_unix_timestamp() -> int:
        """Возвращает текущий UNIX timestamp."""
        return int(time.time())

    @staticmethod
    def timestamp_for_time(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> int:
        """Создает UNIX timestamp для заданного времени."""
        dt = datetime(year, month, day, hour, minute, second)
        return int(dt.timestamp())

    @staticmethod
    def future_timestamp(hours: int = 0, minutes: int = 0, seconds: int = 0) -> int:
        """Возвращает UNIX timestamp для времени, которое наступит через указанное количество времени от сейчас."""
        future_time = datetime.now() + timedelta(hours=hours, minutes=minutes, seconds=seconds)
        return int(future_time.timestamp())

    @staticmethod
    def seconds_since(timestamp: int) -> int:
        """Возвращает количество секунд, прошедших с указанного UNIX timestamp до сейчас."""
        now_ts = int(time.time())
        diff = now_ts - timestamp
        return diff if diff >= 0 else 0

    @staticmethod
    def get_time_difference(past_timestamp: int) -> int:
        """Возвращает разницу между текущим временем и указанным timestamp в секундах."""
        now_ts = int(time.time())
        diff = now_ts - past_timestamp
        return diff

    @staticmethod
    def difference_between_timestamps(ts1: int, ts2: int) -> int:
        """
        Возвращает абсолютную разницу между двумя UNIX timestamp в секундах.
        """
        return abs(ts1 - ts2)

utils = TimeUtils()

wait_moderation = {

}

# ======================
# Телеграм-обработчики
# ======================

async def handle_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global wait_moderation
    query = update.callback_query
    system_id, choice = query.data.split(':')

    if system_id not in wait_moderation:
        await query.answer("Запрос устарел")
        return
    
    user_key = wait_moderation[system_id]

    try:
        if choice == 'approve':
            data = CONFIG_FILE.read()

            data.setdefault('users', {})
            data['users'][system_id] = {
                'user_key': user_key
            }
            CONFIG_FILE.write(data)
            await query.edit_message_text(f"✅ Решение {user_key} принято")
            await query.answer("Решение принято")
        else:
            await query.edit_message_text(f"❌ Решение {user_key} не принято")
            await query.answer("Решение не принято")

    except Exception as e:
        logger.error(f"Error handling moderation: {str(e)}")
        await query.answer("Произошла ошибка")

    finally:
        del wait_moderation[system_id]

async def send_moderation_request(system_id: str, user_key: str, admin_id: int):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Разрешить", callback_data=f"{system_id}:approve"),
        InlineKeyboardButton("❌ Запретить", callback_data=f"{system_id}:deny")
    ]])

    await application.bot.send_message(
        chat_id=admin_id,
        text=f"🚨 Новый запрос доступа\n\n"
                f"Client Hash:\n`{system_id}`\n\n"
                f"User Key:\n`{user_key}`",
        reply_markup=keyboard,
        parse_mode=constants.ParseMode.MARKDOWN_V2
    )

# ======================
# FastAPI Endpoints
# ======================

# @app.post("/notify", status_code=status.HTTP_200_OK)
# async def notify_admin(request: ModerationRequest, x_signature: str = Header(...)):
#     try:
#         # Проверка подписи
#         pass

#         # Отправка модераторам
#         await send_moderation_request(request_id, pending_requests[request_id])

#         return {"status": "success", "request_id": request_id}

#     except Exception as e:
#         logger.error(f"Notification error: {str(e)}")
#         raise HTTPException(status_code=400, detail="Invalid request")
    
@app.post("/register")
async def register(request: RegisterRequest):
    data = CONFIG_FILE.read()

    
    data.setdefault('keys', {})
    data.setdefault('users', {})
    if request.user_key not in data.get('keys'):
        return JSONResponse(
            content={"error": "key_not_exist"},
            status_code=404  # Not Found
        )
    
    if request.system_id in data['users']:
        if data['users'][request.system_id].get('user_key') == request.user_key:
            return JSONResponse(
                content={"status": "moderation_passed"},
                status_code=200
            )

        if request.system_id in wait_moderation:
            del wait_moderation[request.system_id]

    if data['keys'][request.user_key].get('uses') == 0:
        return JSONResponse(
            content={"error": "max_use"},
            status_code=403  # Forbidden
        )
    
    if utils.get_time_difference(data['keys'][request.user_key].get('time_exists', 0)) > 0:
        return JSONResponse(
            content={"error": "time_exists"},
            status_code=403  # Forbidden
        )
    
    if request.system_id in wait_moderation:
        return JSONResponse(
            content={"error": "already_wait_moderation"},
            status_code=403  # Forbidden
        )
    
    if data['keys'][request.user_key].get('uses') != -1:
        data['keys'][request.user_key]['uses'] -= 1
        CONFIG_FILE.write(data)
    
    wait_moderation[request.system_id] = request.user_key
    creator_id = data['keys'][request.user_key]['creator_id']

    await send_moderation_request(request.system_id, request.user_key, creator_id)

    return JSONResponse(
        content={
            "status": "success",
        },
        status_code=200  # OK
    )
    
    # except Exception as e:
    #     logger.error(f"Module error: {str(e)}")
    #     raise HTTPException(status_code=500, detail="Internal server error")
    
@app.post("/get_module")
async def get_module(request: RegisterRequest):
    data = CONFIG_FILE.read()
    try:
        
        data.setdefault('keys', {})
        if request.user_key not in data.get('keys'):
            return JSONResponse(
                content={"error": "key_not_exist"},
                status_code=404  # Not Found
            )

        data.setdefault('users', {})
        if request.system_id not in data.get('users'):
            return JSONResponse(
                content={"error": "user_not_register"},
                status_code=404  # Not Found
            )
        
        if request.user_key != data['users'][request.system_id].get('user_key'):
            return JSONResponse(
                content={"error": "token_not_register"},
                status_code=403  # Not Found
            )
        
        code = ''
        with open(CONFIG_FILE.read()['bot'].get('module'), "r", encoding='utf-8') as f:
            code = f.read()
        
        return JSONResponse(
            content={"status": code},
            status_code=200  # Not Found
        )
    
    except Exception as e:
        logger.error(f"Module error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    

# Command /start
async def handle_command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    args = context.args


    logger.info(f"User {user_id} use command /start {' '.join(args)}")


    if args:
        pass


    await update.message.reply_text(
        "Hello"
    )


# Message processing
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    text = update.message.text


    logger.info(f"User {user_id} sent: {text}")


    await update.message.reply_text(
        text
    )

async def launch_notify(application: Application) -> None:
    if BOT_ADMINS != []:
        try:
            for chat_id in BOT_ADMINS:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Бот успешно запущен"
                )


                logger.info(f'Launch message sent to administrator {chat_id}')


        except Exception as e:
            logger.error(f"[launch_notify()] Error sending message: {str(e)}")

    
    client_handler = threading.Thread(target=run_main)
    client_handler.start()

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error: {context.error}")
    

    if BOT_ADMINS != []:
        try:
            for chat_id in BOT_ADMINS:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ Ошибка в боте: {context.error}"
                )


                logger.error(f'Error message sent to administrator {chat_id}')


        except Exception as e:
            logger.error(f"[error_handler()] Error sending message: {str(e)}")
    
# ======================
# Запуск приложения
# ======================



try:
    application = Application.builder().token(TOKEN).post_init(launch_notify).build()


except Exception as e:
    logger.error(f'[main()] An error occurred while creating the application: {str(e)}')


    exec(1)

handlers = [
    CommandHandler("start", handle_command_start),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
    CallbackQueryHandler(handle_moderation)
]


for handler in handlers:
    application.add_handler(handler)


application.add_error_handler(error_handler)


if TOKEN == "" or TOKEN is None:
        logger.error("[main()] Bot token is not listed in config.json!")
        quit(1)
    

bot = Bot(token=TOKEN)


async def run_web_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        run_web_server()
    )


def run_main():
    asyncio.run(main())


if __name__ == "__main__":

    # Регистрация обработчиков
    application.run_polling()
