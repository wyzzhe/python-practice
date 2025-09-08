class WyzDict():
    def __init__(self, keys, values):
        self._keys = keys
        self._values = values
        self._dict = {}
        self._key_value_list = []
        i = 0
        for key in keys:
            self._dict[key] = values[i]
            i += 1
        length = len(self._keys)
        for i in range(length):
            self._key_value_list.append([self._keys[i], self._values[i]])
    def who(self):
        print("I am wyz's dict")
    def keys(self):
        return self._keys
    def values(self):
        return self._values
    def items(self):
        return self._key_value_list


w_d = WyzDict(["name", "age"], ["Sam", 18])
w_d.who()
for item in w_d.values():
    print(item)

for key, value in w_d.items():
    print(key, value)