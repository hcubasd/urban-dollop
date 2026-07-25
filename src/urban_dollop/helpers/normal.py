import math
import random


def normal_sample(mean=0.0, variance=1.0):
    u1 = 1.0 - random.random()
    u2 = random.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mean + math.sqrt(variance) * z
