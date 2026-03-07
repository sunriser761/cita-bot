import os
import time
import requests
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
URL = "https://icp.administracionelectronica.gob.es/icpco/index"


def send_telegram(msg):
    print("Sending: " + msg)
    for chat_id in CHAT_IDS:
        try:
            url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
            r = requests.post(url, data={"chat_id": chat_id, "text": msg}, timeout=10)
            print("chat_id " + chat_id + ": " + str(r.status_code))
        except Exception as e:
            print("Error: " + str(e))


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
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--single-process")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
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
    time.sleep(5)
    accept_cookies(driver)
    wait = WebDriverWait(driver, 30)
    Select(wait.until(EC.presence_of_element_located((By.ID, "form")))).select_by_value(PROVINCE_VALUE)
    time.sleep(2)
    js_click(driver, driver.find_element(By.ID, "btnAceptar"))
    time.sleep(5)


def select_office_and_tramite(driver):
    print("Step 2: Office and tramite")
    wait = WebDriverWait(driver, 30)
    Select(wait.until(EC.presence_of_element_located((By.ID, "sede")))).select_by_value(OFFICE_VALUE)
    time.sleep(2)
    Select(wait.until(EC.presence_of_element_located((By.NAME, TRAMITE_GROUP)))).select_by_value(TRAMITE_VALUE)
    time.sleep(2)
    js_click(driver, driver.find_element(By.ID, "btnAceptar"))
    time.sleep(5)


def click_enter(driver):
    print("Step 3: Entrar")
    wait = WebDriverWait(driver, 30)
    try:
        js_click(driver, wait.until(EC.presence_of_element_located((By.ID, "btnEntrar"))))
        time.sleep(4)
    except TimeoutException:
        print("btnEntrar not found")


def fill_user_data(driver):
    print("Step 4: NIE and name")
    wait = WebDriverWait(driver, 30)
    nie = wait.until(EC.presence_of_element_located((By.ID, "txtIdCitado")))
    nie.clear()
    nie.send_keys(USER_NIE)
    time.sleep(1)
    name = wait.until(EC.presence_of_element_located((By.ID, "txtDesCitado")))
    name.clear()
    name.send_keys(USER_NAME)
    time.sleep(1)
    js_click(driver, driver.find_element(By.ID, "btnEnviar"))
    time.sleep(5)


def solicitar_cita(driver):
    print("Step 5: Solicitar Cita")
    wait = WebDriverWait(driver, 30)
    try:
        js_click(driver, wait.until(EC.presence_of_element_located((By.ID, "btnEnviar"))))
        time.sleep(5)
    except TimeoutException:
        print("btnEnviar not found")


def check_result(driver):
    page = driver.page_source.lower()
    if "no hay citas disponibles" in page:
        return False
    elif "seleccione fecha" in page or "elija fecha" in page or "calendario" in page:
        return True
    return None


def main():
    send_telegram("Perevirnka citas...")
    driver = create_driver()
    try:
        open_and_select_province(driver)
        select_office_and_tramite(driver)
        click_enter(driver)
        fill_user_data(driver)
        solicitar_cita(driver)
        result = check_result(driver)
        if result is False:
            send_telegram("No citas disponibles")
        elif result is True:
            send_telegram("CITAS AVAILABLE! Book now!")
        else:
            send_telegram("Unknown page state")
    except Exception as e:
        send_telegram("Error: " + str(e))
        print("Error: " + str(e))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
