import subprocess
import shlex
from typing import Dict, Any, List

class TestHarness:
    def __init__(self, policy_data: Dict[str, Any]):
        self.policy = policy_data
        
    def _run_cmd(self, cmd_str: str, expected_success: bool) -> Dict[str, Any]:
        """Runs a real shell command and returns the result."""
        try:
            # We use timeout to avoid hanging indefinitely on dropped packets
            args = shlex.split(cmd_str)
            result = subprocess.run(args, capture_output=True, text=True, timeout=5)
            
            # If expected_success is True, we want returncode == 0
            # If expected_success is False, we want returncode != 0 (e.g., timeout or connection refused)
            success = (result.returncode == 0) == expected_success
            
            status = "PASS" if success else "FAIL"
            
            # Provide helpful actual status based on what happened
            if result.returncode == 0:
                actual = "Success (Connected/Allowed)"
            elif result.returncode == 124 or "Timeout" in str(result.stderr):
                actual = "Timeout (Dropped)"
            else:
                actual = f"Failed (Code {result.returncode}, Refused/Denied)"
                
            return {
                "command": cmd_str,
                "expected": "Success" if expected_success else "Fail/Drop",
                "actual": actual,
                "status": status,
                "output": result.stdout.strip() or result.stderr.strip()
            }
            
        except subprocess.TimeoutExpired:
            success = not expected_success  # If we expected it to fail, a timeout is a pass (Drop)
            status = "PASS" if success else "FAIL"
            return {
                "command": cmd_str,
                "expected": "Success" if expected_success else "Fail/Drop",
                "actual": "Timeout (Dropped)",
                "status": status,
                "output": "Command timed out."
            }
        except Exception as e:
            return {
                "command": cmd_str,
                "expected": "Success" if expected_success else "Fail/Drop",
                "actual": "Execution Error",
                "status": "ERROR",
                "output": str(e)
            }

    def run_tests(self) -> List[Dict[str, Any]]:
        """Executes real network tests to verify policy behavior."""
        results = []
        
        # Test 1: External HTTP to DMZ
        # External attacker tries to reach the web server in the DMZ
        res1 = self._run_cmd("docker exec zone_external curl -v --connect-timeout 2 http://192.168.50.10", expected_success=True)
        res1['name'] = "EXTERNAL (172.20.0.50) -> DMZ (192.168.50.10) [HTTP]"
        results.append(res1)
        
        # Test 2: External SSH to DMZ (Tests DENY rule)
        # Should drop since only HTTP/HTTPS are allowed from EXTERNAL to DMZ
        res2 = self._run_cmd("docker exec zone_external nc -zv -w 2 192.168.50.10 22", expected_success=False)
        res2['name'] = "EXTERNAL (172.20.0.50) -> DMZ (192.168.50.10) [SSH]"
        results.append(res2)
        
        # Test 3: Internal to External (Tests outbound ALLOW)
        # Internal PC tries to reach the external attacker node
        res3 = self._run_cmd("docker exec zone_internal ping -c 1 -W 2 172.20.0.50", expected_success=True)
        res3['name'] = "INTERNAL (10.0.5.10) -> EXTERNAL (172.20.0.50) [ICMP]"
        results.append(res3)
        
        # Test 4: External to Internal (Tests default DROP)
        # External attacker tries to reach the internal network
        res4 = self._run_cmd("docker exec zone_external ping -c 1 -W 2 10.0.5.10", expected_success=False)
        res4['name'] = "EXTERNAL (172.20.0.50) -> INTERNAL (10.0.5.10) [ICMP]"
        results.append(res4)

        return results
