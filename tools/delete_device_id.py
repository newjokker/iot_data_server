import requests
import json

def delete_device(device_id, url="http://8.153.160.138:12345/delete_device_id"):

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "device_id": device_id
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # 如果响应状态码不是200，将抛出HTTPError异常
        
        return response.json()
    
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP错误: {http_err}"
    except requests.exceptions.ConnectionError as conn_err:
        return f"连接错误: {conn_err}"
    except requests.exceptions.Timeout as timeout_err:
        return f"请求超时: {timeout_err}"
    except requests.exceptions.RequestException as req_err:
        return f"请求异常: {req_err}"

# 使用示例
if __name__ == "__main__":
    # 替换为你要删除的设备ID
    device_id_to_delete = "ESP32-DHT11"
    
    # 替换为你的API基础URL
    api_base_url = "http://8.153.160.138:12345/delete_device_id"  # 例如 "http://localhost:8000"
    
    result = delete_device(device_id_to_delete, api_base_url)
    print("删除结果:", result)