import time

import os
from networktables import NetworkTables
from PIL import Image
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")


def render_key_image(deck, icon_filename):

    image = PILHelper.create_image(deck)

    icon = Image.open(ASSETS_PATH + "/" + icon_filename).convert("RGBA")
    icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
    icon_pos = ((image.width - icon.width) // 2, 0)
    image.paste(icon, icon_pos, icon)

    return PILHelper.to_native_format(deck, image)


# As a client to connect to a robot
NetworkTables.initialize(server="127.0.0.1")
time.sleep(3)

sd = NetworkTables.getTable("StreamDeck")

import threading
from StreamDeck.DeviceManager import DeviceManager


def key_change_callback(deck, key, state):
    if state:
        button = buttons[key]
        button.set()


class Button:
    def __init__(self, key):
        self.key = key
        self.active = False

    def set(self):
        sd.putBoolean(f"Action/action{self.key}", True)

    def update(self, deck):
        x = sd.getBoolean(f"Status/status{self.key}", False)
        if x:
            "{}.png".format("Pressed")
            image = render_key_image(deck, "Harold.jpg")
            deck.set_key_image(self.key, image)

        else:
            "{}.png".format("Released")


buttons = []

for i in range(0, 15):
    sd.putBoolean(f"Action/action{i}", False)
    sd.putBoolean(f"Status/status{i}", False)
    button = Button(i)
    buttons.append(button)
streamdecks = DeviceManager().enumerate()

for index, deck in enumerate(streamdecks):
    deck.open()
    deck.reset()
    print(
        "Opened '{}' device (serial number: '{}')".format(
            deck.deck_type(), deck.get_serial_number()
        )
    )

    # Set initial screen brightness to 30%.
    deck.set_brightness(30)
    # Set initial key images.
    # for key in range(deck.key_count()):
    #    update_key_image(deck, key, False)

    # Register callback function for when a key state changes.
    deck.set_key_callback(key_change_callback)

    while True:
        for button in buttons:
            button.update(deck)

    # Wait until all application threads have terminated (for this example,
    # this is when all deck handles are closed).
    for t in threading.enumerate():
        if t is threading.currentThread():
            continue
        if t.is_alive():
            t.join()
