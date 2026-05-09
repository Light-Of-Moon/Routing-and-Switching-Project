import yaml
from pathlib import Path
from typing import Dict, Any

class PolicyParser:
    def __init__(self, policy_path: str):
        self.policy_path = Path(policy_path)

    def parse(self) -> Dict[str, Any]:
        """Parses the YAML policy file and validates basic structure."""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")
            
        with open(self.policy_path, 'r') as f:
            data = yaml.safe_load(f)
            
        self._validate(data)
        return data
        
    def _validate(self, data: Dict[str, Any]):
        """Basic validation of the policy document."""
        required_keys = ['metadata', 'zones', 'rules']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required policy section: {key}")
                
        # Fill in defaults if missing
        if 'services' not in data:
            data['services'] = {}
        if 'nat' not in data:
            data['nat'] = []
            
    def load_services(self) -> Dict[str, Dict[str, Any]]:
        # Map well-known services
        return {
            'HTTP': {'port': 80, 'proto': 'tcp'},
            'HTTPS': {'port': 443, 'proto': 'tcp'},
            'SSH': {'port': 22, 'proto': 'tcp'},
            'FTP': {'port': 21, 'proto': 'tcp'},
            'DNS': {'port': 53, 'proto': 'udp'},
        }
