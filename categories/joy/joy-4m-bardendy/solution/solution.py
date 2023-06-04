from pwn import *
import math
import random
import pyzbar.pyzbar as pyzbar
from PIL import Image
from tqdm import tqdm

MORSE_CODE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    ", ": "--..--",
    ".": ".-.-.-",
    "?": "..--..",
    "/": "-..-.",
    "-": "-....-",
    "(": "-.--.",
    ")": "-.--.-",
}


def morse_decode(message: str) -> str:
    # extra space added at the end to access the
    # last morse code
    message += " "

    decipher = ""
    citext = ""
    for letter in message:
        # checks for space
        if letter != " ":
            # counter to keep track of space
            i = 0

            # storing morse code of a single character
            citext += letter

        # in case of space
        else:
            # if i = 1 that indicates a new character
            i += 1

            # if i = 2 that indicates a new word
            if i == 2:
                # adding space to separate words
                decipher += " "
            else:
                # accessing the keys using their values (reverse of encryption)
                decipher += list(MORSE_CODE_DICT.keys())[
                    list(MORSE_CODE_DICT.values()).index(citext)
                ]
                citext = ""

    return decipher.strip()


def decode_qr(data: str):
    # Set params
    size = round(math.sqrt(len(data)))
    img = Image.new("1", (size, size), color=1)

    pixels = img.load()

    # make qr
    for i in range(len(data)):
        pixels[i % img.size[0], i // img.size[1]] = int(data[i])

    # Make random name and save it
    hex_string = "0123456789abcdef"
    name = "qr_" + "".join([random.choice(hex_string) for x in range(10)])

    resize = img.resize((600, 600))
    resize.save(f"{name}.png")

    # Decoding
    img = Image.open(f"{name}.png")
    morse = pyzbar.decode(img)[0].data.decode()
    return morse


def exploit():
    r = remote("localhost", 1331)

    for i in tqdm(range(250)):
        r.recvline()

        data = r.clean(timeout=0.1).decode().replace("\n", "")

        morse = decode_qr(data)
        res = morse_decode(morse)
        r.sendline(res.encode())
    flag = r.recvline()
    return flag


if __name__ == "__main__":
    
    flag = exploit()
    print(flag.decode())
