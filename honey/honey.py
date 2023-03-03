import logging
import os
import random
import time

from paho.mqtt import client as mqtt_client
from playwright.sync_api import sync_playwright

page_username = os.getenv("USERNAME")
page_password = os.getenv("PASSWORD")

broker = os.getenv("MQTT_BROKER")
port = int(os.getenv("MQTT_PORT", 1883))
topic = os.getenv("MQTT_TOPIC")
client_id = f"python-mqtt-honey-{random.randint(0, 100)}"  # nosec
username = os.getenv("MQTT_USERNAME", "")
password = os.getenv("MQTT_PASSWORD", "")

topic_thermostat_mapping = {
    "street": "HS od ulicy",
    "park": "HS od parku",
}


logging.basicConfig(level=logging.INFO)


def set_thermostat(location, temperature):
    # We want it rounded to the closest 0.5
    desired_temperature = round(float(temperature) * 2) / 2

    requested_temperature = desired_temperature - 20

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://login.keemple.com/login")
        page.locator("#inputIdentity").fill(page_username)
        page.locator("#inputPassword").fill(page_password)
        page.screenshot(path="login-page.png")
        page.locator("#loginButton2").click()

        page.locator("md-menu-sidenav-item:nth-child(2) button").click()
        page.screenshot(path="after-login-page.png")

        while abs(requested_temperature - desired_temperature) > 0.5:
            page.goto("https://login.keemple.com/devices/quick_controls")

            page.locator(
                f'md-whiteframe:has-text("{location}") div.property-control div span span:last-child:has-text("Current")'
            ).hover()
            page.screenshot(path="devices-page.png")

            requested_temperature_locator = f'md-whiteframe:has-text("{location}") div.property-control div span span:first-child'
            requested_temperature = float(page.locator(requested_temperature_locator).all_text_contents()[0].strip().split()[0])

            # The stepping is 0.5 degree
            times = int(abs((requested_temperature - desired_temperature) * 2))

            if desired_temperature > requested_temperature:
                direction = "increment"
            else:
                direction = "decrement"

            button_locator = f'md-whiteframe:has-text("{location}") div.property-control div button[ng-click="{direction}()"]'
            for i in range(times):
                page.locator(button_locator).click()

            time.sleep(1)

            page.goto("https://login.keemple.com/devices/quick_controls")

            page.locator(
                f'md-whiteframe:has-text("{location}") div.property-control div span span:last-child:has-text("Current")'
            ).hover()

            requested_temperature = float(page.locator(requested_temperature_locator).all_text_contents()[0].strip().split()[0])

            page.screenshot(path="after-click-page.png")

        browser.close()


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.warning("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        logging.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        location = msg.topic.split("/")[-2]
        set_thermostat(topic_thermostat_mapping[location], msg.payload.decode())

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == "__main__":
    run()
