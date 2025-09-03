import requests

url = "http://8.153.160.138:12345/agent/create_agent"  # 替换为你的真实地址
data = {
    "name": "test",
    "freq": 10,
    "describe": "这是一个测试的程序"
}

try:
    response = requests.post(url, json=data, timeout=10)
    print("状态码:", response.status_code)
    print("响应内容:", response.text)  # ⬅️ 重点：这里会显示服务端返回的错误详情
except Exception as e:
    print("请求失败:", e)