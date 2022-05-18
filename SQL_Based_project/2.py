temp_list = [[1,2,3], [4,5,6], [7,8,9]]

a = [0,0,0]
b = [0,0,0]
c = [0,0,0]

for x in temp_list:
    a = b
    b = c
    c[0] = x[0]
    c[1] = x[1]
    c[2] = x[2]
    print(a)
    print(b)
    print(c)
    print("_________________")