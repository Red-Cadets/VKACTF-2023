from pwn import remote
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Util.number import *

def get_next_prime(k , p , N , oper):
    i = 0
    res = p + oper
    while i < k:
        if isPrime(res):
            i += 1
            if N % res == 0:
                return res
        res += oper
    return None



host = "212.193.61.73"
port = 13337
r = remote(host , port)


r.recvuntil("Публичный ключ:\n")
public_key = r.recvuntil(b"-----END PUBLIC KEY-----\n")
N = RSA.import_key(public_key).n
e = RSA.import_key(public_key).e
print(f"N = {N}")

r.recvuntil(b": ")
enc_secret = int(r.recvline().strip() , 16)
r.recvuntil(b": ")
nonce = bytes.fromhex(r.recvline().strip().decode())
r.recvuntil(b": ")
enc_message = bytes.fromhex(r.recvline().strip().decode())

r.recvuntil(b": ")
r.sendline(b"1")

r.recvline()

private_key = r.recvuntil(b"-----END RSA PRIVATE KEY-----\n")
params = RSA.import_key(private_key)
p_0 , q_0 = params.p , params.q

p = get_next_prime(10 , p_0 , N , 2)
if p == None:
    p = get_next_prime(10 , p_0 , N , -2)
    print("Tut")

assert p != None

print(f"p = {p}")
q = N // p
d = inverse(e , (p - 1) * (q - 1))
secret = pow(enc_secret , d, N)
secret = long_to_bytes(secret)
print(f"Secret : {secret}")

cipher = AES.new(key = secret ,mode = AES.MODE_GCM , nonce = nonce )
message = cipher.decrypt(enc_message)
print(f"Message: {message}")

r.close()
