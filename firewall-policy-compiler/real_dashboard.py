from flask import Flask, render_template, request, jsonify, Response
import json
import yaml
from policy_parser import PolicyParser
from compiler import Compiler
from nat_dmz import NatDmzGenerator
from vpn_config import VpnConfigGenerator
from auditor import Auditor
from rollback import RollbackManager
from test_harness import TestHarness
import os
import subprocess

import shutil
def get_docker_cmd_list():
    return ["flatpak-spawn", "--host", "docker"] if shutil.which("flatpak-spawn") else ["docker"]

def get_docker_cmd_str():
    return "flatpak-spawn --host docker" if shutil.which("flatpak-spawn") else "docker"

from attack_engine import AttackEngine
from datetime import datetime

# In-memory logging system
SYSTEM_LOGS = []

def add_log(module, action, details):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        "timestamp": timestamp,
        "module": module,
        "action": action,
        "details": details
    }
    SYSTEM_LOGS.insert(0, log_entry) # Put newest on top
    if len(SYSTEM_LOGS) > 500:
        SYSTEM_LOGS.pop()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'firewall_secret'

@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({"success": True, "logs": SYSTEM_LOGS})

@app.route('/system_log', methods=['POST'])
def add_system_log():
    data = request.json
    add_log(data.get('module', 'System'), data.get('action', 'LOG'), data.get('details', 'No details provided'))
    return jsonify({"success": True})

# Initialize paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICIES_DIR = os.path.join(BASE_DIR, 'policies')
SAMPLE_POLICY = os.path.join(POLICIES_DIR, 'sample.yaml')

rollback_mgr = RollbackManager()

def process_policy(yaml_content):
    # Temporarily save to parse
    tmp_file = os.path.join(POLICIES_DIR, 'temp.yaml')
    with open(tmp_file, 'w') as f:
        f.write(yaml_content)
        
    try:
        parser = PolicyParser(tmp_file)
        data = parser.parse()
        services = parser.load_services()
        
        compiler = Compiler(data, services)
        iptables = "\n".join(compiler.compile_iptables())
        nftables = compiler.compile_nftables()
        
        nat_gen = NatDmzGenerator(data)
        nat_rules = "\n".join(nat_gen.generate_iptables_nat())
        
        vpn_gen = VpnConfigGenerator(data, services)
        vpn_config = vpn_gen.generate_wireguard_config()
        
        auditor = Auditor(data)
        audit_report = auditor.run_audit()
        
        return {
            "success": True,
            "iptables": iptables,
            "nftables": nftables,
            "nat": nat_rules,
            "vpn": vpn_config,
            "audit": audit_report
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def index():
    if os.path.exists(SAMPLE_POLICY):
        with open(SAMPLE_POLICY, 'r') as f:
            default_yaml = f.read()
    else:
        default_yaml = "metadata:\n  name: Empty Policy\n"
        
    return render_template('index.html', default_yaml=default_yaml)

@app.route('/device')
def device_dashboard():
    return render_template('device.html')

@app.route('/compile', methods=['POST'])
def compile_policy():
    content = request.json.get('yaml', '')
    result = process_policy(content)
    return jsonify(result)

@app.route('/test', methods=['POST'])
def run_tests():
    content = request.json.get('yaml', '')
    # Process just to parse, normally we'd apply first
    tmp_file = os.path.join(POLICIES_DIR, 'temp.yaml')
    with open(tmp_file, 'w') as f:
        f.write(content)
        
    try:
        parser = PolicyParser(tmp_file)
        data = parser.parse()
        harness = TestHarness(data)
        results = harness.run_tests()
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/snapshot', methods=['POST'])
def snapshot():
    path = rollback_mgr.snapshot()
    return jsonify({"success": True, "path": path})

@app.route('/snapshots', methods=['GET'])
def get_snapshots():
    return jsonify(rollback_mgr.list_snapshots())

@app.route('/interfaces', methods=['GET'])
def get_interfaces():
    try:
        if os.path.exists('/sys/class/net'):
            interfaces = os.listdir('/sys/class/net')
            return jsonify({"success": True, "interfaces": interfaces})
        return jsonify({"success": False, "error": "/sys/class/net not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/nmap_scan', methods=['POST'])
def nmap_scan():
    target = request.json.get('target', '')
    if not target:
        return jsonify({"success": False, "error": "No target specified"})
        
    try:
        # Run a quick scan with nmap from the EXTERNAL zone
        # Using -F for fast scan, -T4 for speed, and --host-timeout to prevent long hangs
        cmd = get_docker_cmd_list() + ["exec", "zone_external", "nmap", "-F", "-T4", "--host-timeout", "10s", target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return jsonify({"success": True, "output": result.stdout, "error_output": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/apply', methods=['POST'])
def apply_policy():
    content = request.json.get('yaml', '')
    result = process_policy(content)
    
    if not result.get('success'):
        return jsonify({"success": False, "error": result.get('error')})
        
    try:
        # Apply iptables rules
        iptables_commands = result.get('iptables', '').split('\n')
        nat_commands = result.get('nat', '').split('\n')
        
        all_commands = iptables_commands + nat_commands
        executed_commands = []
        
        for cmd in all_commands:
            cmd = cmd.strip()
            if not cmd or cmd.startswith('#'):
                continue
            
            # Execute inside the firewall container
            if not cmd.startswith("docker"):
                run_cmd = f"{get_docker_cmd_str()} exec firewall {cmd}"
            else:
                run_cmd = cmd
                
            subprocess.run(run_cmd, shell=True, check=True)
            executed_commands.append(run_cmd)
        
        add_log("Policy Manager", "APPLY", f"Successfully applied {len(executed_commands)} IPTables rules & NAT configurations.")
        return jsonify({"success": True, "message": "Rules successfully applied to the device.", "commands": executed_commands})
    except subprocess.CalledProcessError as e:
        add_log("Policy Manager", "ERROR", f"Failed to apply rules. Shell exception: {e}")
        return jsonify({"success": False, "error": f"Failed to apply rules: {e}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/attack', methods=['POST'])
def run_real_attack():
    # Keep the old endpoint for compatibility or switch entirely to stream. We will keep it.
    target = request.json.get('target', '127.0.0.1')
    try:
        engine = AttackEngine(target)
        output = engine.execute_aggressive_scan()
        return jsonify({"success": True, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/attack_stream')
def attack_stream():
    target = request.args.get('target', '127.0.0.1')
    scenario = request.args.get('scenario', 'aggr_scan')
    
    def generate():
        yield "data: Initializing Advanced Attack Engine...\n\n"
        yield f"data: Target: {target}\n\n"
        yield f"data: Scenario: {scenario.upper()}\n\n"
        yield "data: Executing from EXTERNAL ZONE (172.20.0.50) via Docker...\n\n"
        
        cmd = []
        if scenario == 'aggr_scan':
            yield "data: Using --packet-trace to show RAW packet handling...\n\n"
            cmd = get_docker_cmd_list() + ["exec", "zone_external", "nmap", "-Pn", "-sS", "-T4", "--packet-trace", "--max-retries", "0", "-p", "22,80,443,3306,5432,8080,3389", target]
        elif scenario == 'brute_force':
            yield "data: Simulating SSH Brute-Force against port 22...\n\n"
            cmd = get_docker_cmd_list() + ["exec", "zone_external", "nmap", "-Pn", "--packet-trace", "-p", "22,3389", "--script", "ssh-brute,rdp-enum-encryption", "--script-args", "unpwdb.timelimit=5", target]
        elif scenario == 'unauth_access':
            yield "data: Simulating HTTP unauthorized access brute force (curl storm)...\n\n"
            cmd = get_docker_cmd_list() + ["exec", "zone_external", "nmap", "-Pn", "--packet-trace", "-p", "80,443", "--script", "http-enum,http-title", target]
        elif scenario == 'syn_flood':
            yield "data: Launching SYN Flood / DoS Exhaustion using Nmap packet crafting...\n\n"
            cmd = get_docker_cmd_list() + ["exec", "zone_external", "nmap", "-Pn", "-sS", "--packet-trace", "-p", "80", "-T5", "--max-retries", "0", target]

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                if line:
                    stripped = line.strip()
                    # Telemetry hooks for visual feedback
                    if "SENT (" in stripped:
                        yield f"data: [TELEMETRY]LOG|1\n\n"
                    if "RCVD (" in stripped:
                        if "unreachable" in stripped: # ICMP unreachable (Firewall REJECT)
                            yield f"data: [TELEMETRY]BLOCK|1\n\n"
                        elif "RST" in stripped: # TCP RST (Firewall allowed it, but destination has no service running)
                            yield f"data: [TELEMETRY]ALLOW|1\n\n"
                        elif "SYN" in stripped or "ACK" in stripped:
                            yield f"data: [TELEMETRY]ALLOW|1\n\n"
                    if "filtered" in stripped: # Completely dropped by firewall
                        yield f"data: [TELEMETRY]BLOCK|5\n\n"
                    if "open " in stripped: # Firewall allowed it AND destination is listening
                        yield f"data: [TELEMETRY]ALLOW|5\n\n"
                    if "closed " in stripped: # Firewall allowed it AND hit destination, but no service is listening
                        yield f"data: [TELEMETRY]ALLOW|2\n\n"

                    yield f"data: {stripped}\n\n"
            process.stdout.close()
            process.wait()
            yield "data: \n\ndata: [ATTACK_COMPLETE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"
            
    return Response(generate(), mimetype='text/event-stream')

@app.route('/device_rules', methods=['GET'])
def get_device_rules():
    try:
        # Get detailed iptables output from the firewall container
        result = subprocess.run(get_docker_cmd_list() + ["exec", "firewall", "iptables", "-L", "-v", "-n", "--line-numbers"], capture_output=True, text=True, check=True)
        return jsonify({"success": True, "output": result.stdout})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/device_rules_json', methods=['GET'])
def get_device_rules_json():
    try:
        result = subprocess.run(get_docker_cmd_list() + ["exec", "firewall", "iptables", "-S"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        
        chains = []
        rules = []
        chain_counters = {}
        
        for line in lines:
            if not line: continue
            if line.startswith('-P'):
                # Policy
                parts = line.split(' ')
                chains.append({"chain": parts[1], "policy": parts[2], "raw": line})
            elif line.startswith('-A') or line.startswith('-I'):
                # Rule
                parts = line.split(' ', 2)
                chain = parts[1]
                rule_spec = parts[2] if len(parts) > 2 else ""
                delete_cmd = f"-D {chain} {rule_spec}"
                
                # Calculate rule number based on order for -R (Replace)
                if chain not in chain_counters:
                    chain_counters[chain] = 1
                else:
                    chain_counters[chain] += 1
                    
                rule_num = chain_counters[chain]
                edit_cmd = f"-R {chain} {rule_num} {rule_spec}"
                
                rules.append({
                    "chain": chain,
                    "rule": rule_spec,
                    "raw": line,
                    "rule_num": rule_num,
                    "delete_cmd": delete_cmd,
                    "edit_cmd": edit_cmd
                })
                
        return jsonify({"success": True, "chains": chains, "rules": rules})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/device_rule_action', methods=['POST'])
def device_rule_action():
    action = request.json.get('action') # 'add' or 'delete'
    command = request.json.get('command') # e.g. "-A INPUT -p tcp --dport 80 -j ACCEPT" or "-D INPUT 1"
    
    if not command:
        return jsonify({"success": False, "error": "No command provided"})
        
    try:
        cmd = f"{get_docker_cmd_str()} exec firewall iptables {command}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return jsonify({"success": True, "message": "Rule modified successfully in Firewall container"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.stderr or str(e)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


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
        cmd = get_docker_cmd_list() + ["exec", src_container, "nmap", "-Pn", "-p", str(port), dst_ip, "--max-retries", "1", "--host-timeout", "5s"]
        result = __import__('subprocess').run(cmd, capture_output=True, text=True, timeout=10)
        
        output = result.stdout
        status = "unknown"
        if "open" in output:
            status = "ALLOW (Open)"
        elif "filtered" in output or "drop" in output or "timeout" in output.lower():
            status = "DENY (Blocked/Filtered)"
        elif "closed" in output:
            status = "ALLOW (Port Closed)"
        elif "Host seems down" in output:
            status = "DENY (Host unreachable/Blocked)"
            
        return jsonify({"success": True, "status": status, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/vpn_rule_action', methods=['POST'])
def vpn_rule_action():
    target = request.json.get('target')
    port = request.json.get('port')
    action = request.json.get('action')
    
    cmd_args = ["-I", "FORWARD", "-s", "10.8.0.0/24", "-d", target]
    if port and port.upper() != "ANY":
        cmd_args.extend(["-p", "tcp", "--dport", str(port)])
    cmd_args.extend(["-j", action])
    
    cmd_str = " ".join(cmd_args)
    docker_cmd = f"{get_docker_cmd_str()} exec firewall iptables {cmd_str}"
    
    try:
        subprocess.run(docker_cmd, shell=True, check=True, capture_output=True, text=True)
        return jsonify({"success": True, "message": f"Added Rule: 10.8.0.0/24 -> {target} ({'ANY' if port == 'ANY' else port} TCP) == {action}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/vpn_simulate_stream')
def vpn_simulate_stream():
    target = request.args.get('target', '10.0.5.10')
    test_type = request.args.get('type', 'ping')
    
    def generate():
        yield "data: Initializing VPN Tunnel Access Test...\n\n"
        yield f"data: Target: {target}\n\n"
        yield "data: Origin: Remote Worker VPN Client (10.8.0.10)\n\n"
        
        cmd = []
        if test_type == 'ping':
            yield "data: Sending ICMP Echo Requests through the tunnel...\n\n"
            cmd = get_docker_cmd_list() + ["exec", "zone_vpn", "ping", "-c", "3", "-W", "1", target]
        elif test_type == 'nmap':
            yield "data: Running Nmap Port Scan through the tunnel (--packet-trace)...\n\n"
            cmd = get_docker_cmd_list() + ["exec", "zone_vpn", "nmap", "-Pn", "-sS", "--packet-trace", "-p", "22,80,443,3389,5432", target]
        elif test_type == 'curl':
            yield "data: Performing Layer 7 HTTP Check (cURL)...\n\n"
            cmd = get_docker_cmd_list() + ["exec", "zone_vpn", "curl", "-v", "--max-time", "3", f"http://{target}"]
            
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            output_buffer = ""
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_buffer += line.lower()
                    yield f"data: {line.strip()}\n\n"
                    
            process.stdout.close()
            process.wait()
            
            # Post-Process result
            if test_type == 'ping':
                if "100% packet loss" in output_buffer or "unreachable" in output_buffer:
                    yield "data: [RESULT]|BLOCK\n\n"
                elif " 0% packet loss" in output_buffer:
                    yield "data: [RESULT]|ALLOW\n\n"
                else: 
                    yield "data: [RESULT]|BLOCK\n\n"
                    
            elif test_type == 'nmap':
                if "open" in output_buffer:
                    yield "data: [RESULT]|ALLOW\n\n"
                else:
                    yield "data: [RESULT]|BLOCK\n\n"
                    
            elif test_type == 'curl':
                if "http/1.1 200" in output_buffer or "http/1.1 404" in output_buffer or "html" in output_buffer:
                    yield "data: [RESULT]|ALLOW\n\n"
                else:
                    yield "data: [RESULT]|BLOCK\n\n"
                    
            yield "data: \n\ndata: [TEST_COMPLETE]\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"
            
    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    # Changed port from 5000 to 5001
    app.run(host='0.0.0.0', port=5001, debug=True)
