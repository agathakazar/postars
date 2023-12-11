from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromiumService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

def run_scraper(input_value):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        options=options,
        service=ChromiumService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    )

    stealth(
        driver,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.105 Safari/537.36',
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=False,
        run_on_insecure_origins=False
    )

    url1 = "http://posta.rs/index-stanovnistvo-lat.aspx"
    driver.get(url1)

    time.sleep(1)

    select = Select(driver.find_element(By.ID, "cphMain_cphUsluge_ddlVrstaUsluge"))
    select.select_by_index(1)

    input_field = driver.find_element(By.ID, "cphMain_cphUsluge_tbPratiStatus")
    submit_button = driver.find_element(By.ID, "cphMain_cphUsluge_btnPratiStatus")

#    input_value = "RB272445407SG"
    input_field.send_keys(input_value)

    submit_button.click()

    # results
    span = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "deoSaRezultatima")))

    try:
        span = driver.find_element(By.XPATH, "//span[@class='alert alert-info-posta']")
        if span.get_attribute('innerText') == "Pošiljka nije pronađena. Proverite ispravnost unetog broja.":
            error_message = ["Greska: " + span.get_attribute('innerText'), "", "", "\u00a0"] 
            driver.quit()
            return error_message
        else:
            success_message = ["Gresno: " + span.get_attribute('innerText'), "", "", "\u00a0"]
            driver.quit()
            return success_message

    except Exception as e:
        # raise e
        pass

    try:
        table = driver.find_element(By.XPATH, "//table[@class='table tabela-posta']")
        trs = table.find_elements(By.XPATH, ".//tr")

        results = []
        for tr in trs:
            tds = tr.find_elements(By.XPATH, ".//td[not(self::th)]")
            for td in tds:
                results.append(td.get_attribute('innerText'))
        
        
        driver.quit()
        return results

    except Exception as e:
        # raise e
        driver.quit()
        return None
