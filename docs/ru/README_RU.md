<h1 align="center">Документация</h1>
<div align="center">
    <a href="../README.md">English</a>
    <a href="../ru/README_RU.md">Русский</a>
    <br><br>
</div>
 

# Установка модулей

```bash
python -m pip install -r requirements.txt
```

```bash
git clone https://github.com/Danex-Exe/DataBaze lib/DataBaze/
```

# Настройка конфига

```json
{
    "bot": {
        "token": "Ваш_токен_бота_(Получать_у_@BotFather)",
        "bot_admins": ["Айди_пользователя_1", "Айди_пользователя_2"]
    }
}
```

# Запуск приложения

```bash
python main.py
```

## Примечания
Этот репозиторий — мой базовый шаблон для создания простых ботов Telegram.
В начале у него есть команда /start, а также он повторяет все полученные сообщения.
При возникновении ошибок и при запуске он уведомляет об этом администраторов.
