import os
import threading
import time

from networktables import NetworkTables
from PIL import Image
from PIL.ImageColor import getcolor, getrgb
from PIL.ImageOps import grayscale

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")


def image_tint(src, tint="#ffffff"):  # From https://stackoverflow.com/a/12310820
    if src.mode not in ["RGB", "RGBA"]:
        raise TypeError("Unsupported source image mode: {}".format(src.mode))
    src.load()

    tr, tg, tb = getrgb(tint)
    tl = getcolor(tint, "L")
    if not tl:
        tl = 1
    tl = float(tl)
    sr, sg, sb = map(lambda tv: tv / tl, (tr, tg, tb))
    luts = (
        tuple(map(lambda lr: int(lr * sr + 0.5), range(256)))
        + tuple(map(lambda lg: int(lg * sg + 0.5), range(256)))
        + tuple(map(lambda lb: int(lb * sb + 0.5), range(256)))
    )
    l = grayscale(src)
    if Image.getmodebands(src.mode) < 4:
        merge_args = (src.mode, (l, l, l))
    else:
        a = Image.new("L", src.size)
        a.putdata(src.getdata(3))

        luts += tuple(range(256))

    return Image.merge(*merge_args).point(luts)


ASSETS_PATH = os.path.join(os.path.dirname(__file__), "icons")


def render_key_image(deck, icon_filename):

    image = PILHelper.create_image(deck)

    icon = Image.open(ASSETS_PATH + "/" + icon_filename).convert("RGBA")
    icon.thumbnail((image.width, image.height - 20), Image.LANCZOS)
    icon_pos = ((image.width - icon.width) // 2, 0)
    image.paste(icon, icon_pos, icon)

    return image


def key_change_callback(deck, key, state):
    if state:
        button = buttons[key]
        button.set(deck)


class Button:
    def __init__(self, key):
        self.key = key
        self.active = False

    def set(self, deck):
        sd.putBoolean(f"Action/{self.key}", True)
        self.update(deck)

    def update(self, deck):
        x = sd.getBoolean(f"Status/{self.key}", False)
        y = sd.getBoolean(f"Action/{self.key}", False)
        icon_array = sd.getStringArray("Icons", [])
        name = icon_array[self.key]
        image = None
        if x:
            image = render_key_image(deck, name + "/active.png")
        else:
            image = render_key_image(deck, name + "/inactive.png")
        if y:
            image = image_tint(image, tint="#882020")
        image = PILHelper.to_native_format(deck, image)
        deck.set_key_image(self.key, image)


# As a client to connect to a robot
NetworkTables.initialize(server="10.11.89.2")
# NetworkTables.initialize(server="127.0.0.1")
time.sleep(3)


sd = NetworkTables.getTable("StreamDeck/0")
# a = [
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
#     "default",
# ]
# sd.putStringArray("Icons", a)

buttons = []

for i in range(0, 15):
    sd.putBoolean(f"Action/{i}", False)
    sd.putBoolean(f"Status/{i}", False)
    button = Button(i)
    buttons.append(button)

deck = DeviceManager().enumerate()[0]
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
