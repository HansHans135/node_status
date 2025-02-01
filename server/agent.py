import psutil
import requests
import time
import sys
import config
API_TOKEN = config.api_token

def get_system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)

    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    
    return {
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage
    }

def main():
    panel_url = config.url
    node_id = config.node_id
    
    while True:
        try:
            
            stats = get_system_stats()
            
            
            headers = {'Authorization': f'Bearer {API_TOKEN}'}
            response = requests.post(
                f"{panel_url}/api/nodes/{node_id}/status",
                json=stats,
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"Status updated successfully: {stats}")
            else:
                print(f"Failed to update status: {response.status_code}")
                
        except Exception as e:
            print(f"Error updating status: {e}")
            
            
        time.sleep(10)

if __name__ == '__main__':
    main()