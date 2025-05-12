import requests


SERVER_URL = "http://localhost:8000/notify"


def send_notification(message: str, data: dict = None):
    payload = {
        "message": message,
        "data": data
    }

    
    try:
        response = requests.post(
            SERVER_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )


        return response.json()
    

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    

if __name__ == "__main__":
    result = send_notification(
        message="Тестовое уведомление",
        data={}
    )


    print("Ответ сервера:", result)
