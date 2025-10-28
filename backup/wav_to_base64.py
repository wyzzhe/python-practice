import base64

# 读取WAV文件
with open("credit_to.wav", "rb") as f:
    wav_data = f.read()

# 转换为base64
base64_data = base64.b64encode(wav_data).decode('utf-8')

# 将Base64字符串写入文件
with open("credit_to.txt", "w", encoding="utf-8") as f:
    f.write(base64_data)