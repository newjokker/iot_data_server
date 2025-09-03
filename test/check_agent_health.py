import requests

# url = "http://8.153.160.138:12345/agent/health_check/test"  
url = "http://8.153.160.138:12345/agent/health_check/*"  


try:
    response = requests.get(url, timeout=10)
    print("状态码:", response.status_code)
    print("响应内容:", response.text)  # ⬅️ 重点：这里会显示服务端返回的错误详情
except Exception as e:
    print("请求失败:", e)
    
