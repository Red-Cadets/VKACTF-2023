#!/usr/bin/ python3

from Crypto.Random import get_random_bytes
from Crypto.Util.number import bytes_to_long, long_to_bytes
import numpy as np
from pwn import *


def gcd_extended(num1, num2):
    
    if num1 == 0:
        return (num2, 0, 1)
    else:
        div, x, y = gcd_extended(num2 % num1, num1)
    return (div, y - (num2 // num1) * x, x)


def recovery_Matr(gamma): #Данную функцию восстановления матрицы необходимо запускать в ядре SageMath
    N = 256
    assert len(gamma) == 30
    Matr = Matrix(Zmod(N) ,  [gamma[:5],gamma[5:10],gamma[10:15],gamma[15:20],gamma[20:25]])
    A = []
    for i in range(5):
        b = [gamma[ 5 + i ] , gamma[10 + i] , gamma[15 + i], gamma[20 + i], gamma[25 + i]  ]
        b = vector(Zmod(N) , b)
        try:
            a = Matr.solve_right(b)
            A.append(a)
        except:
            continue
    A_ = Matrix(Zmod(N) , A)
    X0 = vector(Zmod(N) , gamma[:5])
    print(A_)
    seed = (A_ ^ (-1)) * X0
    return A , seed



s = remote('212.193.61.73', 2440)

s.recvuntil(b'N enc_gamma: ')
N = int(s.recvline())
print(f'N = {N}')
s.recvuntil(b': ')
e_1 = int(s.recvline())
print(f'e_1 = {e_1}')

payload = get_random_bytes(256)
s.recvuntil(b': ')
s.sendline(b'1')
s.recvuntil(b': ')
s.sendline(payload.hex().encode())
s.recvuntil(b': ')
e_2 = int(s.recvline())
print(f'e_2 = {e_2}')
s.recvuntil(b': ')
ciphertext_1 = bytes.fromhex(str(s.recvline())[2:-3])

s.recvuntil(b': ')
s.sendline(b'1')
s.recvuntil(b': ')
s.sendline(payload.hex().encode())
s.recvuntil(b': ')
s.recvuntil(b': ')
ciphertext_2 = bytes.fromhex(str(s.recvline())[2:-3])

enc_gamma_1 = xor(ciphertext_1, payload)
enc_gamma_2 = xor(ciphertext_2, payload)

num_enc_gamma_1 = bytes_to_long(enc_gamma_1)
num_enc_gamma_2 = bytes_to_long(enc_gamma_2)

div, a, b = gcd_extended(e_1, e_2)

dec_gamma = (pow(num_enc_gamma_1, a, N) * pow(num_enc_gamma_2, b, N)) % N
gamma = long_to_bytes(dec_gamma)[:30]

gamma_int = []
for i in range(0, len(gamma)):
    gamma_int.append((gamma[i]))
print(gamma_int)

s.interactive()
matr = np.matrix(recovery_Matr(gamma_int))

print(matr)
key = '' #Сюда подставить ключ, полученный из recovery_key.sage

s.sendline(key)

FLAG = s.recvlline()

print(f"FLAG: {FLAG}")