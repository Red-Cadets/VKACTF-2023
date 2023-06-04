#!/usr/bin/ python3

from string import ascii_letters, digits
from Crypto.Random import get_random_bytes, random
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256, SHA512
from Crypto.Cipher import AES
from Crypto.Util.number import long_to_bytes, bytes_to_long, inverse, getStrongPrime, getRandomRange
from Crypto.Util.Padding import pad, unpad
from Crypto.Util import Counter
import json

# Peach password and salt
SALT = get_random_bytes(8) 
PASS = "".join([random.choice(ascii_letters + digits) for _ in range(20)]).encode()
nonce = random.randint(0, (2**128)-1)

FLAG = open("SuperSecretflag.txt" , "rb").read()

class Client:
    def __init__(self, password, salt):
        self.password = password
        self.salt = salt
        self.gen_keys()
        self.cipher_enc = AES.new(self.enc_key, AES.MODE_ECB)
        self.counter = Counter.new(128, initial_value=nonce)
        self.cipher_master = AES.new(self.master_key, AES.MODE_CTR, counter=self.counter)
        self.prepare_crypto_material()

    def gen_keys(self):
        keys = PBKDF2(self.password, self.salt, 32,
                      count=1000, hmac_hash_module=SHA512)
        self.enc_key, self.auth_key = keys[:16], keys[16:]
        self.auth_key_hashed = SHA256.new(self.auth_key).hexdigest()
        self.master_key = get_random_bytes(16)
        self.share_key_pub, self.share_key = self.generate_elgamal_parameters(1024)

    def generate_elgamal_parameters(self, key_size):
        parameters = {}

        while True:
            p = getStrongPrime(key_size)
            if len(bin(p)[2:]) == key_size:
                break

        parameters['p'] = p

        g = getRandomRange(1, p-1)
        parameters['g'] = g

        while True:
            x = getRandomRange(1, p-1)
            if len(bin(x)[2:]) == key_size:
                break
        parameters['x'] = x

        y = pow(g, x, p)
        parameters['y'] = y
        
        pub_key = (parameters['y'], parameters['g'], parameters['p'])
        return pub_key, parameters

    def prepare_crypto_material(self):
        self.master_key_enc = self.cipher_enc.encrypt(self.master_key)
        self.share_key_enc = self.cipher_master.encrypt(self.format_elgamal_privkey())
        

    def format_elgamal_privkey(self):
        data = self.format_number(self.share_key['x'])
        return pad(data, 16)

    def format_number(self, num):
        num_bytes = long_to_bytes(num)
        num_bin = bin(num)
        return long_to_bytes(len(num_bin), 2) + num_bytes

    def get_encrypted_flag(self):
        secret = SHA256.new(long_to_bytes(self.share_key['x'])).digest()
        ct = AES.new(secret, AES.MODE_ECB).encrypt(pad(FLAG, 16))
        return ct


class Client_new_login:
    def __init__(self, password, salt, share_key_pub):
        self.share_key_pub = share_key_pub
        self.password = password
        self.salt = salt
        self.gen_keys()
        self.cipher_enc = AES.new(self.enc_key, AES.MODE_ECB)

    def gen_keys(self):
        keys = PBKDF2(self.password, self.salt, 32,
                      count=1000, hmac_hash_module=SHA512)
        self.enc_key, self.auth_key = keys[:16], keys[16:]
        self.auth_key_hashed = SHA256.new(self.auth_key).hexdigest()

    def login_step2(self, SID_enc, share_key_enc, master_key_enc):
        self.master_key = self.cipher_enc.decrypt(master_key_enc)
        self.counter = Counter.new(128, initial_value=nonce)
        self.cipher_master = AES.new(self.master_key, AES.MODE_CTR, counter=self.counter)
        share_key = unpad(self.cipher_master.decrypt(share_key_enc), 16)
        len_x, x = self.parse_elgamal_privkey(share_key)
        SID = self.EG_CRT_decrypt(SID_enc, len_x, x)
        return SID

    def EG_CRT_decrypt(self, ciphertext, len_x, x):
        p = self.share_key_pub[2]
        a = int(ciphertext[0])
        b = int(ciphertext[1])
        x = int(bin(x)[:len_x], 2)
        m = (b * (inverse(pow(a, x, p), p))) % p 
        return long_to_bytes(m)

    def parse_elgamal_privkey(self, share_key):
        
        len_x = bytes_to_long(share_key[:2])
        x = bytes_to_long(share_key[2:])

        return len_x, x

class Challenge():
    def __init__(self):
        self.C = Client(PASS, SALT)
        self.C_ = None
        material = json.dumps({"auth_key_hashed": self.C.auth_key_hashed, "master_key_enc": self.C.master_key_enc.hex(), "share_key_pub": self.C.share_key_pub, "share_key_enc": self.C.share_key_enc.hex()})
        print(f"Регистрируется Принцесса Пич :\nEmail : beauty_peach@RC.рф\nUsername : Princess_Peach\nNew client is uploading crypto material...\n{material}\n")
        self.current_step = "PROCESSING"
        self.max_payload_size = 8192
        self.start()

    def challenge(self, message):
        if not "action" in message:
            self.exit = True
            {"error": "Please choose an action."}

        if message["action"] == "wait_login":
            self.current_step = "LOGIN"
            self.before_send = f"Login attempt from Peach:\n"
            self.C_ = Client_new_login(PASS, SALT, self.C.share_key_pub)
            return {"auth_key_hashed": self.C_.auth_key_hashed}

        elif message["action"] == "block":
            if self.current_step != "LOGIN":
                self.exit = True
                return {"error": "Wrong order"}
            self.current_step = "PROCESSING"
            return {"message": "User was successfully blocked."}

        elif message["action"] == "send_challenge":
            if self.current_step != "LOGIN":
                self.exit = True
                return {"error": "Wrong order"}
            self.current_step = "PROCESSING"
            if not "SID_enc" in message or not "share_key_enc" in message or not "master_key_enc" in message:
                return {"error": "Please provide the encrypted SID, share_key and master_key."}
            else:
                try:
                    SID_enc = [0, 0]
                    SID_enc[0] = int(message["SID_enc"][0])
                    SID_enc[1] = int(message["SID_enc"][1])
                    share_key_enc = bytes.fromhex(message["share_key_enc"])
                    master_key_enc = bytes.fromhex(message["master_key_enc"])
                    return {"SID": self.C_.login_step2(SID_enc, share_key_enc, master_key_enc).hex()}
                except Exception as e:
                    return {"error": "An error occured during the login."}

        elif message["action"] == "get_encrypted_flag":
            return {"encrypted_flag": self.C.get_encrypted_flag().hex()}

        else:
            return {"error": "This is not a valid action."}
    
    def start(self):
        while True:
            try: 
                message = json.loads(input())
                print(self.challenge(message))
            except:
                print({"Error": "Invalid JSON format"})


if __name__ == "__main__":
    chal = Challenge()
    chal.start()
    exit()
