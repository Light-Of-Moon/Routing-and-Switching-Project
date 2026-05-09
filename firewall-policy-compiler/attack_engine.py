import subprocess

class AttackEngine:
    def __init__(self, target: str):
        self.target = target
        
    def execute_syn_flood(self) -> str:
        """Runs a real SYN flood attack using hping3 for 5 seconds."""
        cmd = ["docker", "exec", "zone_external", "timeout", "5", "hping3", "-S", "-p", "80", "--flood", "--rand-source", self.target]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # hping3 outputs to stderr mostly
            output = result.stderr.strip() or result.stdout.strip()
            return f"--- Real SYN Flood Attack Launched from EXTERNAL ZONE (172.20.0.50) (5s) ---\nTarget: {self.target}\nResult:\n{output}\n\n(Check your Device Rules Dashboard to see the DROP packet counters increment rapidly!)"
        except Exception as e:
            return f"Failed to execute SYN flood: {str(e)}"

    def execute_aggressive_scan(self) -> str:
        """Runs an aggressive stealth SYN scan using Nmap."""
        # -sS (SYN Scan), -T5 (Insane speed), -O (OS Detection), -sV (Service Detection)
        cmd = ["docker", "exec", "zone_external", "nmap", "-sS", "-T5", "-O", "-sV", "--max-retries", "1", self.target]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip() or result.stderr.strip()
            return f"--- Aggressive Nmap Scan Launched from EXTERNAL ZONE (172.20.0.50) ---\nTarget: {self.target}\nResult:\n{output}"
        except subprocess.TimeoutExpired:
            return f"Aggressive scan against {self.target} timed out (likely blocked by firewall)."
        except Exception as e:
            return f"Failed to execute scan: {str(e)}"
