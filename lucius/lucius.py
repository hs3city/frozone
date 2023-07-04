import logging
import os
import random
import time
import traceback

from paho.mqtt import client as mqtt_client
from playwright.sync_api import sync_playwright

page_username = os.getenv("USERNAME")
page_password = os.getenv("PASSWORD")

broker = os.getenv("MQTT_BROKER")
port = int(os.getenv("MQTT_PORT", 1883))
main_topic = os.getenv("MQTT_TOPIC")
client_id = f"python-mqtt-lucius-{random.randint(0, 100)}"  # nosec
username = os.getenv("MQTT_USERNAME", "")
password = os.getenv("MQTT_PASSWORD", "")

thermostat_topic_mapping = {
    "HS od ulicy": "pracownia/thermostat_street",
    "HS od parku": "pracownia/thermostat_park",
}


logging.basicConfig(level=logging.INFO)


def get_thermostat_data(thermostat_topic_mapping):
    thermostat_data = {}

    try:
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

            page.goto("https://login.keemple.com/devices/quick_controls")

            for thermostat in thermostat_topic_mapping:
                page.locator(
                    f'md-whiteframe:has-text("{thermostat}") div.property-control div span span:last-child:has-text("Current")'
                ).hover()
                page.screenshot(path="devices-page.png")

                measured_temperature_locator = f'md-whiteframe:has-text("{thermostat}") div[on="serviceName"] div p'
                measured_temperature = page.locator(measured_temperature_locator).all_text_contents()[0].strip().split()[0]
                requested_temperature_locator = (
                    f'md-whiteframe:has-text("{thermostat}") div.property-control div span span:first-child'
                )
                requested_temperature = page.locator(requested_temperature_locator).all_text_contents()[0].strip().split()[0]
                current_temperature_locator = (
                    f'md-whiteframe:has-text("{thermostat}") div.property-control div span span:last-child'
                )
                current_temperature = page.locator(current_temperature_locator).all_text_contents()[0].strip().split()[1]

                topic = f"{main_topic}/{thermostat_topic_mapping[thermostat]}"

                thermostat_data[topic] = {
                    "measured": measured_temperature,
                    "requested": requested_temperature,
                    "current": current_temperature,
                }

            browser.close()
    except Exception:
        logging.error(traceback.format_exc())

    return thermostat_data


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


def publish(client, topic, payload):
    result = client.publish(topic, payload)
    status = result[0]
    if status == 0:
        logging.info(f"Send `{payload}` to topic `{topic}`")
    else:
        logging.warning(f"Failed to send message to topic {topic}")


def run():
    client = connect_mqtt()
    client.loop_start()
    while True:
        thermostat_data = get_thermostat_data(thermostat_topic_mapping)
        for topic in thermostat_data:
            measured = thermostat_data[topic]["measured"]
            requested = thermostat_data[topic]["requested"]
            current = thermostat_data[topic]["current"]
            publish(client, topic, measured)
            location = topic.split("_")[-1]
            topic = f"thermostat/pracownia/{location}/requested"
            publish(client, topic, requested)
            topic = f"thermostat/pracownia/{location}/current"
            publish(client, topic, current)
        time.sleep(60)


if __name__ == "__main__":
    run()
