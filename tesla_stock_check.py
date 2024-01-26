from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import subprocess
from plyer import notification
import platform

def send_imessage(phone_number, message):
    script = './send_imsg.scpt'
    subprocess.run(['osascript', script, phone_number, message])
    
def notify(title, msg):
    if "Windows" == platform.system():
        notification.notify(
            title=title,
            message=msg,
            app_name='Tesla Stock Check'
        )

    if "Darwin" == platform.system():
        script = f'display notification "{msg}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])
        send_imessage(mobile_phone, msg)

def check_stock(driver, url):
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, "addToCartBtn")))
        html = driver.page_source

        # save the web page to file
        # with open('./webpage.html', 'w', encoding='utf-8') as file:
        #    file.write(html)
        soup = BeautifulSoup(html, 'html.parser')

        # search SKU
        product_title = soup.find("h2", class_='product-title tds-text--h1-alt').contents[0]
        section = soup.find("section", {"id": "productInfo"})
        product_model = section.get("data-productmodelsizelistjson")
        print(f"{product_title} SKUs: {product_model}")

        # try to select a SKU and add it to cart    
        dropdown_xpath = '//*[@id="product-color-select-desktop"]'
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_xpath)))
        dropdown.click()
        
        # select model
        model_xpath = '/html/body/main/div[1]/div/section[1]/div[1]/div[3]/div/div[2]/fieldset/div/div[2]/div/div[2]/select/option[2]'
        model_option = wait.until(EC.element_to_be_clickable((By.XPATH, model_xpath)))
        sku_name = model_option.text
        time.sleep(1)
        model_option.click()
    except Exception as e:
        return "fail"
    
    try:
        # check "AddToCart" status    
        wait1 = WebDriverWait(driver, 15)
        addtocart_xpath = "//div[contains(@class, 'active')]//input[@id='addToCartBtn']"
        add_to_cart = wait1.until(EC.element_to_be_clickable((By.XPATH, addtocart_xpath)))
        # delay 1s
        time.sleep(1)
        add_to_cart.click()     
        msg_in_stock = f'{product_title} {sku_name} in stock, added to cart!!'         
        print(msg_in_stock)
        notify(product_title, msg_in_stock)
        time.sleep(5)
        # close the popup window /html/body/main/div[1]/div/div[2]/dialog/div[1]/button
        close_btn_xpath = '/html/body/main/div[1]/div/div[2]/dialog/div[1]/button'
        close_btn = wait.until(EC.element_to_be_clickable((By.XPATH, close_btn_xpath)))
        time.sleep(1)
        close_btn.click()
    except TimeoutException:
        # AddToCart button is not clickable
        print(f"{product_title} {sku_name} Sold out!")
    except Exception as e:
        print(f"Warn: Checking failed: {e}" )
        return "fail"
        
    try:
        # check another SKU  
        time.sleep(5)        
        driver.refresh()  
        dropdown_xpath = '//*[@id="product-color-select-desktop"]'
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_xpath)))
        dropdown.click()

        model_xpath = '/html/body/main/div[1]/div/section[1]/div[1]/div[3]/div/div[2]/fieldset/div/div[2]/div/div[2]/select/option[3]'
        model_option = wait.until(EC.element_to_be_clickable((By.XPATH, model_xpath)))
        sku_name = model_option.text
        time.sleep(1)
        model_option.click()

        # add another SKU to cart   //*[@id="addToCartBtn"]
        # addtocart_xpath = '//*[@id="addToCartBtn"]'
        addtocart_xpath = "//div[contains(@class, 'active')]//input[@id='addToCartBtn']"
        add_to_cart = wait.until(EC.element_to_be_clickable((By.XPATH, addtocart_xpath)))
        # add_to_cart = driver.find_element('xpath', addtocart_xpath)
        time.sleep(1)
        add_to_cart.click()                      
        msg_in_stock = f'{product_title} {sku_name} in stock, added to cart!!'    
        print(msg_in_stock)
        notify(product_title, msg_in_stock)
        return "success"
    except TimeoutException:
        # AddToCart button is not clickable
        print(f"{product_title} {sku_name} Sold out!")
        return "soldout"
    except Exception as e:
        print(f"Warn: Checking failed: {e}" )
 
    return "fail"


url_puddle = "https://shop.tesla.cn/product/model-y-puddle-light"
url_cart = "https://shop.tesla.cn/cart"
mobile_phone = "+8613999999999"
check_interval = 10
hold_time = 1800
 
chrome_options = Options()

# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
driver = webdriver.Chrome(options=chrome_options)

while True:    
    result = check_stock(driver, url_puddle)
    if 'soldout' == result:
        print(f"Sold out, Sleep {check_interval}s then check again...")
        time.sleep(check_interval)            
    if 'fail' == result:
        print("Warn: Checking failed, please check the network or update this code.")
        break
    if 'success' == result:
        time.sleep(10)
        driver.get(url_cart)
        msg = "Congratulations: Added to cart, please login with your Tesla account and checkout it!"
        notify("Tesla", msg)       
        break

time.sleep(hold_time)
driver.quit()