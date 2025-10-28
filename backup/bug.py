try:
    f = open('linux', 'r', encoding="UTF-8")
except FileNotFoundError as e:
    print("")
    f = open('linux', 'w', encoding="UTF-8")

print(name)