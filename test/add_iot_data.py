
import requests

url = "http://8.153.160.138:12345/data/iot_data"  

payload = {
    "device_id": "test",  
    "temperature": 23.5,
    "humidity": 65.0,
    "timestamp": "2024-06-01T12:00:00",
    "location": "room_101"
}


try:
    response = requests.post(url, timeout=10, json=payload)
    print("状态码:", response.status_code)
    print("响应内容:", response.text)  # ⬅️ 重点：这里会显示服务端返回的错误详情
except Exception as e:
    print("请求失败:", e)
    






