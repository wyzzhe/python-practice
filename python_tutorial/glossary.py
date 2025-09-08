class Device:
    def play(self):
        print("music")

class CDPlayer(Device):
    ...

class iPod(Device):
    ...

class Phone(Device):
    ...

def play_music(device):
    flag = "duck"
    if flag == "duck":
        if hasattr(device, "play"):
            device.play()
        else:
            print(f"{device} play 个蛋")
    else:
        if isinstance(device, (CDPlayer, iPod, Phone)):
            device.play()
        else:
            raise TypeError("Unsupported device")

device = CDPlayer()

if __name__ == "__main__":
    play_music(device)
    try:
        play_music(1)
    except Exception as e:
        print(f"error: {e}")
    print("接着奏乐, 接着舞~")
    print("接着奏乐, 接着舞~")
    print("接着奏乐, 接着舞~")
