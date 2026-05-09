import re

with open('real_dashboard.py', 'r') as f:
    content = f.read()

# Inject helper functions
helper_code = """
import shutil
def get_docker_cmd_list():
    return ["flatpak-spawn", "--host", "docker"] if shutil.which("flatpak-spawn") else ["docker"]

def get_docker_cmd_str():
    return "flatpak-spawn --host docker" if shutil.which("flatpak-spawn") else "docker"
"""

if "def get_docker_cmd_list():" not in content:
    content = content.replace("import subprocess", "import subprocess\n" + helper_code)

# Replace string versions
content = content.replace('"flatpak-spawn --host docker exec firewall', 'get_docker_cmd_str() + " exec firewall')
content = content.replace('f"flatpak-spawn --host docker exec firewall {cmd}"', 'f"{get_docker_cmd_str()} exec firewall {cmd}"')
content = content.replace('f"flatpak-spawn --host docker exec firewall iptables {command}"', 'f"{get_docker_cmd_str()} exec firewall iptables {command}"')

# Replace list versions
content = content.replace('["flatpak-spawn", "--host", "docker", "exec",', 'get_docker_cmd_list() + ["exec",')

with open('real_dashboard.py', 'w') as f:
    f.write(content)
print("Dashboard fixed!")
