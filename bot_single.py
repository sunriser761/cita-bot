import requests
import time

TELEGRAM_TOKEN = "8644017899:AAHlIz_JNgZNlvUo3nu3wI3YQWsp06aA8kw"
CHAT_IDS = ["1375932609", "7370463142", "371058744"]
USER_NIE = "Y9497446R"
USER_NAME = "SYDORENKO MATVII"
PROVINCE = "38"
TRAMITE = "4112"
SEDE = "99"

BASE_URL = "https://icp.administracionelectronica.gob.es/icpco"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Connection": "keep-alive",
}


def send_telegram(msg):
    print("Sending: " + msg)
    for chat_id in CHAT_IDS:
        try:
            url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
            r = requests.post(url, data={"chat_id": chat_id, "text": msg}, timeout=10)
            print("chat_id " + chat_id + ": " + str(r.status_code))
        except Exception as e:
            print("Error: " + str(e))


def check_citas():
    session = requests.Session()
    session.headers.update(HEADERS)

    # Крок 1: відкрити головну сторінку
    print("Step 1: Opening main page")
    r = session.get(BASE_URL + "/index", timeout=30)
    print("Status: " + str(r.status_code))

    # Крок 2: вибір провінції
    print("Step 2: Selecting province")
    data = {
        "form": "/icpco/citar?p=" + PROVINCE + "&locale=es",
        "method": "acInfo"
    }
    r = session.post(BASE_URL + "/index.html", data=data, timeout=30)
    print("Status: " + str(r.status_code))
    time.sleep(1)

    # Крок 3: вибір офісу та трамітe
    print("Step 3: Selecting office and tramite")
    data = {
        "sede": SEDE,
        "tramiteGrupo[1]": TRAMITE,
        "method": "acEntrar"
    }
    r = session.post(BASE_URL + "/acInfo", data=data, timeout=30)
    print("Status: " + str(r.status_code))
    time.sleep(1)

    # Крок 4: натиснути Entrar
    print("Step 4: Entrar")
    data = {"method": "acEntrar"}
    r = session.post(BASE_URL + "/acEntrar", data=data, timeout=30)
    print("Status: " + str(r.status_code))
    time.sleep(1)

    # Крок 5: ввести NIE і ім'я
    print("Step 5: NIE and name")
    data = {
        "rdbTipoDoc": "nie",
        "txtIdCitado": USER_NIE,
        "txtDesCitado": USER_NAME,
        "method": "acVerFormulario"
    }
    r = session.post(BASE_URL + "/acEntrada", data=data, timeout=30)
    print("Status: " + str(r.status_code))
    time.sleep(1)

    # Крок 6: запит на cita
    print("Step 6: Solicitar cita")
    data = {"method": "acCitar"}
    r = session.post(BASE_URL + "/acCitar", data=data, timeout=30)
    print("Status: " + str(r.status_code))

    page = r.text.lower()

    if "no hay citas disponibles" in page:
        return False
    elif "seleccione fecha" in page or "elija fecha" in page or "calendario" in page:
        return True
    else:
        print("Unknown page, length: " + str(len(page)))
        return None


def main():
    send_telegram("Perevirnka citas (requests mode)...")
    try:
        result = check_citas()
        if result is False:
            send_telegram("No citas disponibles")
        elif result is True:
            send_telegram("CITAS AVAILABLE! Book now!")
        else:
            send_telegram("Unknown page state - check logs")
    except Exception as e:
        send_telegram("Error: " + str(e))
        print("Error: " + str(e))


if __name__ == "__main__":
    main()
