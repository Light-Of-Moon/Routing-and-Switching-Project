import sys
import argparse
from attack_engine import AttackEngine

def main():
    parser = argparse.ArgumentParser(description='Firewall Policy Compiler - Real Attack Testing Tool')
    parser.add_argument('target', help='Target IP or hostname to attack (e.g., 127.0.0.1 or 192.168.1.5)')
    parser.add_argument('--type', choices=['synflood', 'scan'], default='scan', 
                        help='Type of attack to run: "synflood" (hping3) or "scan" (aggressive nmap)')
    
    args = parser.parse_args()
    
    print(f"Initializing attack engine against target: {args.target}")
    engine = AttackEngine(args.target)
    
    if args.type == 'synflood':
        print("Launching SYN Flood (Requires sudo/root)...")
        output = engine.execute_syn_flood()
    else:
        print("Launching Aggressive Nmap Scan (Requires sudo/root)...")
        output = engine.execute_aggressive_scan()
        
    print("\n" + "="*50)
    print("ATTACK OUTPUT:")
    print("="*50)
    print(output)
    print("="*50)

if __name__ == "__main__":
    main()
