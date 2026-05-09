from typing import Dict, Any, List

class VpnConfigGenerator:
    def __init__(self, policy_data: Dict[str, Any], services: Dict[str, Any] = None):
        self.policy = policy_data
        self.zones = policy_data.get('zones', {})
        self.vpn_subnet = self.zones.get('VPN', '10.8.0.0/24')
        self.rules = policy_data.get('rules', [])
        self.services = services or {}
        
    def _resolve_ip(self, target: str) -> str:
        """Resolve a zone name or IP address to an actual IP/subnet."""
        if target == 'ANY':
            return '0.0.0.0/0'
        return self.zones.get(target, target)

    def _resolve_service(self, svc_name: str) -> Dict[str, Any]:
        """Resolve a service name to port/proto."""
        return self.services.get(svc_name, {'port': svc_name, 'proto': 'tcp'})

    def generate_wireguard_config(self) -> str:
        """Generates a complete WireGuard server config for secure remote access."""
        
        # Hardcoded realistic keys for lab simulation purposes
        server_priv = "aNbhgL/T2T2Kk6P5J1w/4qK4mP+Z0M/XvC+0iM8O1W4="
        server_pub  = "oQxy+6C8o5g/gW4QcZh+eBwVfS/2B1mGz8H8A8mD3U="
        client_priv = "cJvXv0s0q3E/5H6BfS3kZ+Z1jK9w/R9a7T8A1s4F7C4="
        client_pub  = "xUjVzR9a7T8A1s4F7C4cJvXv0s0q3E/5H6BfS3kZ+Z1="
        
        post_up_rules = [
            "# POST-UP: Configure NAT and explicit subnet access controls",
            f"PostUp = iptables -I INPUT -p udp --dport 51820 -j ACCEPT"
        ]
        
        post_down_rules = [
            "# POST-DOWN: Clean up routing rules",
            f"PostDown = iptables -D INPUT -p udp --dport 51820 -j ACCEPT"
        ]
        
        allowed_ips = set()
        
        for rule in self.rules:
            if rule.get('source') == 'VPN':
                dst = self._resolve_ip(rule.get('destination', 'ANY'))
                action = 'ACCEPT' if str(rule.get('action', '')).upper() == 'ALLOW' else 'DROP'
                
                svcs = rule.get('service', ['ANY'])
                if isinstance(svcs, str):
                    svcs = [svcs]
                    
                for svc in svcs:
                    rule_cmd = f"-i wg0 -d {dst}"
                    if svc != 'ANY':
                        s_details = self._resolve_service(svc)
                        proto = s_details['proto']
                        port = s_details['port']
                        rule_cmd += f" -p {proto} --dport {port}"
                    
                    rule_cmd += f" -j {action}"
                    
                    post_up_rules.append(f"PostUp = iptables -I FORWARD {rule_cmd}")
                    post_down_rules.append(f"PostDown = iptables -D FORWARD {rule_cmd}")
                    
                    if action == 'ACCEPT' and dst != '0.0.0.0/0':
                        allowed_ips.add(dst)
                        
        post_up_rules.append(f"PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")
        post_down_rules.append(f"PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE")
        
        allowed_ips_str = ", ".join(list(allowed_ips)) if allowed_ips else self.vpn_subnet
        
        lines = [
            "# ==========================================",
            "# WIREGUARD VPN SERVER CONFIGURATION (wg0)",
            "# ==========================================",
            "[Interface]",
            f"Address = {self.vpn_subnet.replace('.0/24', '.1/24')}",
            "ListenPort = 51820",
            f"PrivateKey = {server_priv}",
            ""
        ] + post_up_rules + [
            ""
        ] + post_down_rules + [
            "",
            "## -----------------------------------------",
            "## CLIENT PEER DEVICE CONFIGURATION",
            "## -----------------------------------------",
            "[Peer]",
            f"PublicKey = {client_pub}",
            f"AllowedIPs = {self.vpn_subnet.replace('.0/24', '.2/32')}",
            "",
            "# (Below is the config snippet for the External Client Device)",
            "# [Interface]",
            f"# PrivateKey = {client_priv}",
            f"# Address = {self.vpn_subnet.replace('.0/24', '.2/24')}",
            "# [Peer]",
            f"# PublicKey = {server_pub}",
            f"# AllowedIPs = {allowed_ips_str}, {self.vpn_subnet} # Only route Allowed subnets",
            "# Endpoint = <FIREWALL_EXTERNAL_IP>:51820",
        ]
        return "\n".join(lines)
