from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import random
import os
from datetime import datetime

# Configuration
CONFIG = {
    "li_at_cookie": "YOUR_LI_AT_COOKIE_HERE",
    "message": "Hi {name}, thanks for connecting! I'd love to learn more about your work in {industry}.",
    "data_file": "linkedin_connections.json",
    "daily_message_limit": 20
}

class ConnectionAcceptorBot:
    def __init__(self):
        self.driver = self.setup_driver()
        self.connections = self.load_connections()

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver

    def load_connections(self):
        if os.path.exists(CONFIG["data_file"]):
            with open(CONFIG["data_file"], "r") as f:
                return json.load(f)
        return {}

    def save_connections(self):
        with open(CONFIG["data_file"], "w") as f:
            json.dump(self.connections, f, indent=2)

    def login(self):
        self.driver.get("https://www.linkedin.com")
        self.driver.add_cookie({
            'name': 'li_at',
            'value': CONFIG["li_at_cookie"],
            'domain': '.linkedin.com'
        })
        self.driver.refresh()
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "global-nav__me")))

    def check_new_acceptances(self):
        """Check connections page for new acceptances"""
        print("\n🔍 Checking for new connection acceptances...")
        self.driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
        time.sleep(random.uniform(3, 5))

        # Scroll to load all connections
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Get all current connections
        current_connects = set()
        for element in self.driver.find_elements(By.CSS_SELECTOR, ".mn-connection-card a.mn-connection-card__link"):
            profile_url = element.get_attribute("href").split('?')[0]
            current_connects.add(profile_url)

        # Update status for any new acceptances
        updated = False
        for profile_url in list(self.connections.keys()):
            if (not self.connections[profile_url]["accepted"] 
                and profile_url in current_connects):
                
                self.connections[profile_url]["accepted"] = True
                self.connections[profile_url]["date_accepted"] = datetime.now().strftime("%Y-%m-%d")
                print(f"🎉 New acceptance: {self.connections[profile_url]['name']}")
                updated = True

        if updated:
            self.save_connections()

    def send_followups(self):
        """Send messages to newly accepted connections"""
        print("\n📩 Sending follow-up messages...")
        messages_sent = 0

        for profile_url, data in self.connections.items():
            if (data["accepted"] 
                and not data["message_sent"] 
                and messages_sent < CONFIG["daily_message_limit"]):
                
                try:
                    self.driver.get(f"{profile_url}?greeting=1")
                    time.sleep(random.uniform(3, 5))

                    message_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "msg-form__contenteditable")))
                    
                    msg = CONFIG["message"].format(
                        name=data["name"].split()[0],
                        industry=data.get("keyword", "your industry")
                    )
                    message_box.send_keys(msg)
                    time.sleep(1)
                    self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
                    
                    self.connections[profile_url]["message_sent"] = True
                    messages_sent += 1
                    print(f"✉️ Sent to {data['name']}")
                    time.sleep(random.uniform(10, 15))

                except Exception as e:
                    print(f"⚠️ Failed to message {data['name']}: {str(e)}")
                    continue

        if messages_sent > 0:
            self.save_connections()

    def run(self):
        try:
            self.login()
            self.check_new_acceptances()
            self.send_followups()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            self.driver.save_screenshot('error.png')
        finally:
            self.driver.quit()
            print("\n🏁 Follow-up bot completed!")

if __name__ == "__main__":
    bot = ConnectionAcceptorBot()
    bot.run() 