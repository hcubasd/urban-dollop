import math
import random


def _box_muller():
    u1 = 1.0 - random.random()
    u2 = random.random()
    z1 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    z2 = math.sqrt(-2.0 * math.log(u1)) * math.sin(2.0 * math.pi * u2)
    return z1, z2


def t(nu=3):
    normals = []
    while len(normals) < nu + 1:
        z1, z2 = _box_muller()
        normals.append(z1)
        if len(normals) < nu + 1:
            normals.append(z2)
    z = normals[0]
    v = sum(x * x for x in normals[1:])
    return z / math.sqrt(v / nu)
