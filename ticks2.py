import math
print(round(0.257896))


def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier


print(round_down(0.2547896, 2))
