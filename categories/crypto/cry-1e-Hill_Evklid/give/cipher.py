#!/usr/bin/ python3

from binascii import unhexlify
from random import randint
from Crypto.Util.number import bytes_to_long, getPrime , long_to_bytes
import numpy as np

intro = ("""   

          !GPPPPPPPP?                                                                   
          P@@@@@@@@@#                                                                   
       @@@7      ^!~J@@@@@@P                                                            
   .!!7PGG~      :^:!###GPGY!!!                                                         
   J@@@   .^:::::::::^^^   ~@@@.                                                        
G##J^^^::::^:!#&&7:^^~~~:..:^^^G###########BB#########BBB##########BB###!               
@@@J   ^^^~7!?&&&Y!7!~~~^:^.   #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&&&&&&@Y...            
&@@J   :::G@@&   G@@&~~~^::::::^~~^::^^~^~~~~~~~^:^^^^^^~~^::::^^.      ?@@&            
&@@5 ..:::G@@#   G@@&~~~^:::^^^^^^^^^^^~~^^^^^^^^^^:::::^:!P55^:::......5@@@            
&@@P::::::G@@#   G@@&~~~^::^^^^^~^~!!!!!!^::::::^~~^::::::?@@@!::^~^~!!~G@@@            
@@@G:^^:::^!~7&&&J~!~^^^:::^~~~&@@@@@@@@@@&@@@@@&&@#777#&&G...B&@P:::777B@@@            
G##P???^:::::~&&&7::::::^^^~YJJB################@@@&7?7&@@B   &@@B^^^7?7B@@@            
   J@@@~^^::::::::::::::^~~5@@@.                G@@&777&@@B   &@@#77777!B@@@            
   .!!7B##?^^^^^^^^^7BBB###P!!!                 :!!?#&&J!!^   ^!!Y&&&&&&5!!~            
       &@@P!7777777!Y@@@@@@5                       .@@@:         !@@@@@@?               
          P@@@@@@@@@#                                                                   
          !GPPPPPPPP?                                                                   
          
          """)

FLAG = open("SuperSecretflag.txt" , "rb").read()
KEY = open("SuperSecretkey.txt" , "rb").read()

class Stream_cipher():
    def __init__(self, M):
        print(intro)
        self.A = np.matrix(M)
        self.K = 256
        self.x0 = [[randint(0,self.K)] for i in range(5)]
        self.p = getPrime(1024)
        self.q = getPrime(1024)
        self.N = self.p * self.q
        print(f"N enc_gamma: {self.N}")
        self.gen_gamma()

    def gen_gamma(self):
        X0 = self.x0
        gamma = []
        lenght = 255
        for i in range(0,lenght,5):
            X = self.A * X0 % 256
            X0 = X
            gamma.extend(list(X))

        gamma = [int(i) for i in gamma]
        byte_gamma = bytearray(gamma)
        print("\n !GENERATE NEW ENC_GAMMA! \n")
        long_gamma = bytes_to_long(byte_gamma)
        m = long_gamma
        self.e = getPrime(1024)
        print(f"e enc_gamma: {self.e}")
        self.enc_gamma = pow(m , self.e , self.N)
        self.enc_gamma = long_to_bytes(self.enc_gamma)

    def encrypt(self , pt):
        ct = b""
        
        while True:
            if len(self.enc_gamma) == 0:
                self.gen_gamma()
            if len(pt) == 0:
                break
            ct += bytes( [ pt[0] ^ self.enc_gamma[0] ])
            pt = pt[1:]
            self.enc_gamma = self.enc_gamma[1:]
        return ct 
 
    def decrypt(self,ct):
        return self.encrypt(ct)
    
def check_input(phrase):
    while True:
        try:
            your_input = int(input(phrase))
            break
        except:
            print("Invalid int format")
    return your_input

def check_input_hex(phrase):
    while True:
        try:
            your_input = unhexlify(input(phrase))
            break
        except:
            print("Invalid hex format")
    return your_input.hex()

def gen_M():

    key = list(KEY)
    M = []
    for i in range(0, len(key), 5):
        M.append(list(key[i:i+5]))
    return M

M = gen_M()
cipher = Stream_cipher(M)

while True:

    print()
    print("[1] - Зашифровать текст")
    print("[2] - Расшифровать текст")
    print("[3] - Получить флаг")
    print("[0] - Выход")
    print()

    your_input = check_input("Выберите действие: ")

    if your_input == 1:

        pt = check_input_hex("Исходный текст: ")

        ct = cipher.encrypt(bytes.fromhex(pt))
        print(f"Шифротекст: {ct.hex()}")   

    elif your_input == 2:

        ct = check_input_hex("Исходный текст:  ")
        pt = cipher.decrypt(bytes.fromhex(ct))
        print(f"Шифротекст: {pt.hex()}")

    elif your_input == 3:
        input_password = input("Введите ключ: ")

        if input_password.encode() == KEY:
            print(FLAG)
        else:
            print("Ключ неверный!")      

    elif your_input == 0:
        print("Игра окончена . . .")
        exit()

