import re

with open('real_dashboard.py', 'r') as f:
    content = f.read()

new_route = """
@app.route('/connectivity_test', methods=['POST'])
def connectivity_test():
    data = request.json
    source = data.get('source')
    dest = data.get('destination')
    port = data.get('port')
    
    if not all([source, dest, port]):
        return jsonify({"success": False, "error": "Missing required fields"})
        
    containers = {
        'EXTERNAL': 'zone_external',
        'INTERNAL': 'zone_internal',
        'DMZ': 'zone_dmz',
        'VPN': 'zone_vpn'
    }
    
    ips = {
        'EXTERNAL': '172.20.0.50',
        'INTERNAL': '10.0.5.10',
        'DMZ': '192.168.50.10',
        'VPN': '10.8.0.10'
    }
    
    src_container = containers.get(source)
    dst_ip = ips.get(dest)
    
    if not src_container or not dst_ip:
        return jsonify({"success": False, "error": "Invalid zones specified"})
        
    try:
        cmd = ["flatpak-spawn", "--host", "docker", "exec", src_container, "nmap", "-Pn", "-p", str(port), dst_ip, "--max-retries", "1", "--host-timeout", "5s"]
        result = __import__('subprocess').run(cmd, capture_output=True, text=True, timeout=10)
        
        output = result.stdout
        status = "unknown"
        if "open" in output:
            status = "ALLOW (Open)"
        elif "filtered" in output or "drop" in output or "timeout" in output.lower():
            status = "DENY (Blocked/Filtered)"
        elif "closed" in output:
            status = "CLOSED"
        elif "Host seems down" in output:
            status = "DENY (Host unreachable/Blocked)"
            
        return jsonify({"success": True, "status": status, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

"""

if "def connectivity_test():" not in content:
    content = content.replace("if __name__ == '__main__':", new_route + "\nif __name__ == '__main__':")
    with open('real_dashboard.py', 'w') as f:
        f.write(content)
