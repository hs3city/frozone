import logging
import os
import random
import traceback

import asyncio_mqtt as aiomqtt
import discord
from discord import app_commands

discord_token = os.getenv("DISCORD_TOKEN")

broker = os.getenv("MQTT_BROKER")
port = int(os.getenv("MQTT_PORT", 1883))
main_topic = os.getenv("MQTT_TOPIC")
client_id = f"python-mqtt-frozone-{random.randint(0, 100)}"  # nosec
username = os.getenv("MQTT_USERNAME", "")
password = os.getenv("MQTT_PASSWORD", "")

thermostats = ["street", "park"]

# Logging configuration
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(
    name="temperatura",
    description="Ustaw temperaturę",
    guild=discord.Object(id=779727338002186261),
)
async def set_temperature(interaction: discord.Interaction, value: float):
    keybearer = False
    for role in interaction.user.roles:
        if "Klucznicy" in role.name:
            keybearer = True
    reason = ""
    if not keybearer:
        reason = "Nie jesteś Klucznikiem."
    elif value < 15 or value > 30:
        reason = f"Wybierz zakres od 15 do 30 ({value} nie pyknie)."
    if keybearer and 15 <= value <= 30:
        try:
            async with aiomqtt.Client(broker) as client:
                for thermostat in thermostats:
                    topic = f"{main_topic}/{thermostat}/set"
                    logging.info(f"Sending to {topic}: {value} (on request of {interaction.user.name})")
                    await client.publish(topic, payload=value)
        except Exception:
            logging.error(traceback.format_exc())

        await interaction.response.send_message(f"Temperatura ustawiona na {value} (+/- 0.5°C). Miłego pobytu!")
    else:
        await interaction.response.send_message(
            f"Przykro mi, {interaction.user.name}, obawiam się, że nie mogę tego zrobić.\n{reason}"
        )


@client.event
async def on_ready():
    for guild in client.guilds:
        logging.info(f"{client.user} has connected to Discord server {guild} (ID: {guild.id})!")
        await tree.sync(guild=guild)


client.run(discord_token)
