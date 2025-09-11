import traceback

def l3():
    return 1 / 0

def l2():
    l3()

def l1():
    l2()

try:
    print(l1())

except Exception:
    print(traceback.format_exc())