from Crypto.Cipher import AES, Blowfish, DES3
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from Crypto.Util.Padding import unpad


def decrypt_blowfish(ciphertext, key):
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    padded_plaintext = cipher.decrypt(ciphertext)
    return padded_plaintext


def decrypt_des3_ecb(ciphertext, key):
    cipher = DES3.new(key, DES3.MODE_ECB)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext


def decrypt_aes(ciphertext, key):
    cipher = AES.new(key, AES.MODE_ECB)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext


# Key's data
key_xor = open('key_xor', 'rb').read()
key_blowfish = open('key_blowfish', 'rb').read()
key_aes = open('key_aes', 'rb').read()
key_des3 = open('key_des3', 'rb').read()

# Encrypt data
data_xor = open('data_xor', 'rb').read()
data_blowfish = open('data_blowfish', 'rb').read()
data_aes = open('data_aes', 'rb').read()
data_des3 = open('data_des3', 'rb').read()

# XOR
result_xor = b''

for i in range(len(data_xor)):
    result_xor += bytes([data_xor[i] ^ key_xor[i % len(key_xor)]])

with open('something.png', 'wb') as f:
    f.write(result_xor)

# Blowfish
decrypted = decrypt_blowfish(data_blowfish, key_blowfish)

with open('interesting.png', 'wb') as f:
    f.write(decrypted)

# AES
decrypted = decrypt_aes(data_aes, key_aes)
with open('inside.png', 'wb') as f:
    f.write(decrypted)

# DES3
decrypted = decrypt_des3_ecb(data_des3, key_des3)
with open('this.png', 'wb') as f:
    f.write(decrypted)
