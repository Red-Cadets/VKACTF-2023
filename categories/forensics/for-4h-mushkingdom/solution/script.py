from Crypto.Cipher import AES


def decrypt_aes(ciphertext, key):
    cipher = AES.new(key, AES.MODE_ECB)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext


key_aes = open('key_day42', 'rb').read()
data_aes = open('data_day42', 'rb').read()

decrypted = decrypt_aes(data_aes, key_aes)
with open('day42.txt', 'wb') as f:
    f.write(decrypted)
