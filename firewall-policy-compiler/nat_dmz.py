from typing import Dict, Any, List

class NatDmzGenerator:
    def __init__(self, policy_data: Dict[str, Any]):
        self.nat_rules = policy_data.get('nat', [])
        self.zones = policy_data.get('zones', {})
        
    def _resolve_ip(self, target: str) -> str:
        return self.zones.get(target, target)

    def generate_iptables_nat(self) -> List[str]:
        commands = []
        if not self.nat_rules:
            return commands
            
        commands.append("# NAT/DMZ Generated Rules")
        commands.append("iptables -t nat -F")
        
        for rule in self.nat_rules:
            rtype = rule.get('type')
            if rtype == 'SNAT':
                src = self._resolve_ip(rule.get('source', 'ANY'))
                out_if = rule.get('out_interface', 'eth0')
                cmd = f"iptables -t nat -A POSTROUTING -s {src} -o {out_if} -j MASQUERADE"
                commands.append(cmd)
            elif rtype == 'DNAT':
                in_if = rule.get('in_interface', 'eth0')
                port = rule.get('port')
                to_ip = rule.get('to_ip')
                # Defaults to TCP for demo
                cmd = f"iptables -t nat -A PREROUTING -i {in_if} -p tcp --dport {port} -j DNAT --to-destination {to_ip}:{port}"
                commands.append(cmd)
                
        return commands
