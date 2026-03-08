import os
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

TELEGRAM_TOKEN = "8644017899:AAHlIz_JNgZNlvUo3nu3wI3YQWsp06aA8kw"
CHAT_IDS = ["1375932609", "7370463142", "371058744"]
USER_NIE = "Y9497446R"
USER_NAME = "SYDORENKO MATVII"
PROVINCE_VALUE = "/icpco/citar?p=38&locale=es"
OFFICE_VALUE = "99"
TRAMITE_GROUP = "tramiteGrupo[1]"
TRAMITE_VALUE = "4112"
CHECK_INTERVAL = 600
URL = "https://icp.administracionelectronica.gob.es/icpco/index"


def send_telegram(msg):
    print("Sending: " + msg)
    for chat_id in CHAT_IDS:
        try:
            url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
            r = requests.post(url, data={"chat_id": chat_id, "text": msg}, timeout=10)
            print("chat_id " + chat_id + ": " + str(r.status_code))
        except Exception as e:
            print("Telegram error: " + str(e))


def js_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", element)


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # На Railway Chrome встановлений системно
    chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
    chromedriver_bin = os.environ.get("CHROMEDRIVER_BIN", None)

    if chromedriver_bin:
        service = Service(chromedriver_bin)
    else:
        service = Service(ChromeDriverManager().install())

    options.binary_location = chrome_bin
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
    )
    return driver


def accept_cookies(driver):
    try:
        cookie = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "cookie_action_close_header"))
        )
        js_click(driver, cookie)
        time.sleep(1)
    except TimeoutException:
        pass


def open_and_select_province(driver):
    print("Step 1: Province")
    driver.get(URL)
    time.sleep(4)
    accept_cookies(driver)
    wait = WebDriverWait(driver, 20)
    Select(wait.until(EC.presence_of_element_located((By.ID, "form")))).select_by_value(PROVINCE_VALUE)
    time.sleep(1)
    js_click(driver, driver.find_element(By.ID, "btnAceptar"))
    time.sleep(4)


def select_office_and_tramite(driver):
    print("Step 2: Office and tramite")
    wait = WebDriverWait(driver, 20)
    Select(wait.until(EC.presence_of_element_located((By.ID, "sede")))).select_by_value(OFFICE_VALUE)
    time.sleep(1)
    Select(wait.until(EC.presence_of_element_located((By.NAME, TRAMITE_GROUP)))).select_by_value(TRAMITE_VALUE)
    time.sleep(1)
    js_click(driver, driver.find_element(By.ID, "btnAceptar"))
    time.sleep(4)


def click_enter(driver):
    print("Step 3: Entrar")
    wait = WebDriverWait(driver, 20)
    try:
        js_click(driver, wait.until(EC.presence_of_element_located((By.ID, "btnEntrar"))))
        time.sleep(3)
    except TimeoutException:
        print("btnEntrar not found")


def fill_user_data(driver):
    print("Step 4: NIE and name")
    wait = WebDriverWait(driver, 20)
    nie = wait.until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    nie.clear()
    nie.send_keys(USER_NIE)
    time.sleep(0.5)
    name = wait.until(EC.presence_of_element_located((By.ID, "txtDesCitado")))
    name.clear()
    name.send_keys(USER_NAME)
    time.sleep(0.5)
    js_click(driver, driver.find_element(By.ID, "btnEnviar"))
    time.sleep(4)


def solicitar_cita(driver):
    print("Step 5: Solicitar Cita")
    wait = WebDriverWait(driver, 20)
    try:
        js_click(driver, wait.until(EC.presence_of_element_located((By.ID, "btnEnviar"))))
        time.sleep(4)
    except TimeoutException:
        print("btnEnviar not found")


def check_result(driver):
    page = driver.page_source.lower()
    if "no hay citas disponibles" in page:
        return False
    elif "seleccione fecha" in page or "elija fecha" in page or "calendario" in page:
        return True
    return None


def run_check(driver):
    open_and_select_province(driver)
    select_office_and_tramite(driver)
    click_enter(driver)
    fill_user_data(driver)
    solicitar_cita(driver)
    return check_result(driver)


def main():
    print("Bot started")
    send_telegram("Bot started - monitoring TARJETA CONFLICTO UCRANIA")
    driver = create_driver()
    last_status = None
    check_count = 0

    while True:
        now = datetime.now().strftime("%H:%M:%S")
        try:
            result = run_check(driver)
            check_count += 1

            if result != last_status or check_count % 6 == 0:
                if result is False:
                    msg = "[" + now + "] No citas disponibles"
                elif result is True:
                    msg = "[" + now + "] CITAS AVAILABLE! Book now!"
                else:
                    msg = "[" + now + "] Unknown page state"
                print(msg)
                send_telegram(msg)
                last_status = result

            if result is True:
                send_telegram("Bot stopped - appointment found!")
                break

        except TimeoutException as e:
            print("Timeout: " + str(e))
            send_telegram("Timeout, restarting browser")
            try:
                driver.quit()
            except Exception:
                pass
            driver = create_driver()

        except Exception as e:
            print("Error: " + str(e))
            send_telegram("Error: " + str(e))
            try:
                driver.quit()
            except Exception:
                pass
            time.sleep(30)
            driver = create_driver()

        print("Next check in " + str(CHECK_INTERVAL) + "s")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
