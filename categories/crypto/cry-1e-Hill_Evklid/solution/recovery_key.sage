#!/usr/bin/ python3

def recovery_Matr(gamma):
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
    seed = (A_ ^ (-1)) * X0
    return A


gamma = [23, 147, 206, 171, 77, 91, 182, 144, 35, 177, 154, 138, 35, 92, 106, 118, 48, 247, 125, 139, 188, 185, 135, 169, 168, 92, 85, 147, 133, 63]

matr = Matrix(recovery_Matr(gamma))


key = ''
for i in matr:
    for j in i:
        key += (chr(j))

print(f"KEY: {key}")

