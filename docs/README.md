<h1 align="center">Documentation</h1>
<div align="center">
    <a href="README.md">English</a>
    <a href="ru/README_RU.md">Русский</a>
    <br><br>
</div>
 

# Installing modules

```bash
python -m pip install -r requirements.txt
```

```bash
git clone https://github.com/Danex-Exe/DataBaze lib/DataBaze/
```

# Setting up the config

```json
{
    "bot": {
        "token": "Your_Bot_Token_(Get_from_@BotFather)",
        "bot_admins": ["User_ID_1", "User_ID_2"]
    }
}
```

# Launching the application

```bash
python main.py
```

## Notes
This repository is my basic template for creating simple telegram bots.
At the beginning it has a /start command, and it also repeats all received messages.
When errors occur and when it starts, it notifies administrators about it.
