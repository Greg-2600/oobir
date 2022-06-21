def runningSums(lst):
    res = [lst[0]]
    for elem in lst[1:]:
        res.append(res[-1] + elem)
    return res
def antiRunningSums(lst):
    res = [lst[0]]
    for i in range(1,len(lst)):
        res.append(lst[i] - lst[i-1])
    return res
def predict(lst):
    deriv = 0
    while True:
        nxt = antiRunningSums(lst)
        if sum(map(abs, nxt)) > sum(map(abs, lst)):
            break
        lst = nxt
        deriv += 1
    lst.append(lst[-1])
    for i in range(deriv):
        lst = runningSums(lst)
    return lst

# Example call. Correctly gives back [1,4,9,16,25,36,49].
#print(predict([1,4,9,16,25,36]))
print(predict([0,1,1,2,3,5,8,13,21,34]))
