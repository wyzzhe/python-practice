_list = []

_list.append(1)

_list.extend([2, 3, 4])

_list.insert(1, 9)

_list.pop(3)

# _list.clear()

print(_list)
copy_list = _list.copy()
_list[1] = 0
print(_list)
print(copy_list)

print(_list)
_list.sort()
print(_list)
_list.reverse()
print(_list)

del _list[0]
print(_list)