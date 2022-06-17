import numpy as np

temp_list = [100, 150, 185]
print(temp_list[-1])
avg = 10

def distance_from_mean(level):
    print(f'abs difference list: {[abs(level - y) < avg for y in temp_list]}')
    print(f'sum: {np.sum([abs(level - y) < avg for y in temp_list])}')
    print(np.sum([abs(level - y) < avg for y in temp_list]) == 0)
    return np.sum([abs(level - y) < avg for y in temp_list]) == 0


if distance_from_mean(105):
    print(105)
