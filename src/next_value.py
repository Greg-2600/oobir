def running_sums(lst):
    """running sums"""
    res = [lst[0]]
    for elem in lst[1:]:
        res.append(res[-1] + elem)
    return res


def anti_running_sums(lst):
    """anti running sums"""
    res = [lst[0]]
    for i in range(1,len(lst)):
        res.append(lst[i] - lst[i-1])
    return res


def predict(lst):
    """predict"""
    derive = 0
    while True:
        nxt = anti_running_sums(lst)
        if sum(map(abs, nxt)) > sum(map(abs, lst)):
            break
        lst = nxt
        derive += 1
    lst.append(lst[-1])
    for i in range(derive):
        lst = running_sums(lst)
    return lst

# Example call. Correctly gives back [1,4,9,16,25,36,49].
# print(predict([1,4,9,16,25,36]))

# Fibonacci
print(predict([0, 1, 1, 2, 3, 5, 8, 13, 21, 34]))
