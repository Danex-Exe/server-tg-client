import importlib.util
import logging
import threading
import asyncio


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


# Проверки исправности модулей
def check_dependencies():
    required = ['telegram', 'fastapi', 'lib.DataBaze.DataBaze']
    for lib in required:
        if not importlib.util.find_spec(lib.replace('.', '/')):
            logger.error(f"Не установлен модуль: {lib}")
            exit(1)


from telegram import (
    Update,
    Bot,
    constants, 
    ReplyKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application, 
    PicklePersistence,
    ApplicationBuilder,
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler, 
    filters, 
    ContextTypes
)

from lib.DataBaze.DataBaze import DataBaze
from fastapi import FastAPI, status
from pydantic import BaseModel
import httpx
import uvicorn


DATABAZE = DataBaze(path="data/")
CONFIG_FILE = DATABAZE.file(name='config', type="json")
DEFAULT_CONFIG = {
    "bot": {
        "token": "",
        "bot_admins": []
    },
    "users": {}
}
app = FastAPI()


class NotificationRequest(BaseModel):
    message: str
    data: dict = None


CONFIG_FILE_CREATE_RESULT = CONFIG_FILE.create(DEFAULT_CONFIG)
match CONFIG_FILE_CREATE_RESULT:
    case 'file_exists':
        if CONFIG_FILE.info()['size'] <= 2:
            print(CONFIG_FILE.info()['size'])
            logger.warning("Файл конфигурации бота пуст")

            CONFIG_FILE.write(DEFAULT_CONFIG)

            logger.info("В файл конфигурации бота была записана базовая конфигурация")
    
    case 'success':
        logger.info("Файл конфигурации создан")
        logger.info("В файл конфигурации записана базовая конфигурация")

    case 'error':
        logger.error("Произошла ошибка при создании конфигурационного файла")

    case _:
        logger.warning(f"Получен неизвестный ответ при создании конфигурационного файла: {CONFIG_FILE_CREATE_RESULT}")


TOKEN = CONFIG_FILE.read().get('bot', {}).get('token')
BOT_ADMINS = CONFIG_FILE.read().get('bot', {}).get('bot_admins', [])


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


@app.post("/notify", status_code=status.HTTP_200_OK)
async def notify_admin(request: NotificationRequest):
    try:
        message = f"Новое уведомление:\n{request.message}"


        if request.data:
            message += f"\nДанные: {request.data}"

            
        await Bot(token=TOKEN).send_message(chat_id=BOT_ADMINS[0], text=message)

        
        return {"status": "success", "message": "Notification sent"}
    

    except Exception as e:
        return {"status": "error", "message": str(e)}


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


# Launch notification
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


try:
    application = Application.builder().token(TOKEN).post_init(launch_notify).build()


except Exception as e:
    logger.error(f'[main()] An error occurred while creating the application: {str(e)}')


    exec(1)


# Registering handlers
handlers = [
    CommandHandler("start", handle_command_start),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
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
    application.run_polling()