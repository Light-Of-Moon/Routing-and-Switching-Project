import os
import shutil
from datetime import datetime
from typing import Dict, Any, List

class RollbackManager:
    def __init__(self, backup_dir="/tmp/fw_backups"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def snapshot(self) -> str:
        """Takes a snapshot of current iptables rules."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"iptables_{timestamp}.save")
        
        # In a real environment: os.system(f"iptables-save > {backup_file}")
        # For our demo/safe mode:
        with open(backup_file, "w") as f:
            f.write("# Dummy iptables-save backup\n")
            f.write(f"# Snapshot taken at {timestamp}\n")
            f.write("*filter\n:INPUT ACCEPT [0:0]\nCOMMIT\n")
            
        return backup_file
        
    def restore(self, backup_file: str) -> bool:
        """Restores from a given snapshot."""
        if not os.path.exists(backup_file):
            return False
            
        # In a real environment: os.system(f"iptables-restore < {backup_file}")
        # For demo:
        print(f"Restored iptables from {backup_file}")
        return True
        
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots."""
        snapshots = []
        for file in os.listdir(self.backup_dir):
            if file.endswith(".save"):
                full_path = os.path.join(self.backup_dir, file)
                stat = os.stat(full_path)
                snapshots.append({
                    "filename": file,
                    "path": full_path,
                    "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        return sorted(snapshots, key=lambda x: x['timestamp'], reverse=True)
