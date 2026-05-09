from typing import Dict, Any, List

class Auditor:
    def __init__(self, policy_data: Dict[str, Any]):
        self.policy = policy_data
        self.zones = policy_data.get('zones', {})
        self.rules = policy_data.get('rules', [])
        
    def run_audit(self) -> Dict[str, Any]:
        """Runs all audit checks and returns a report."""
        report = {
            'shadowing': self._check_shadowing(),
            'broad_permits': self._check_broad_permits(),
            'score': 100
        }
        
        # Calculate a basic score based on findings
        deductions = len(report['shadowing']) * 10 + len(report['broad_permits']) * 5
        report['score'] = max(0, 100 - deductions)
        
        return report
        
    def _check_shadowing(self) -> List[str]:
        """Detect if a rule completely shadows a subsequent rule."""
        shadow_warnings = []
        # Simplified shadowing check: 
        # A DENY rule for ANY/ANY shadows everything after it for the same protocol
        # A broad ALLOW rule shadows specific DENY rules later
        for i, r1 in enumerate(self.rules):
            for j in range(i + 1, len(self.rules)):
                r2 = self.rules[j]
                
                # If r1 allows ALL to ALL, and r2 is specific, r2 is shadowed
                if (r1.get('source') in ['ANY', 'EXTERNAL'] and 
                    r1.get('destination') == 'ANY' and 
                    r1.get('action') == 'ALLOW'):
                    shadow_warnings.append(f"Rule '{r1.get('name')}' may shadow '{r2.get('name')}'")
                    break
                    
        return list(set(shadow_warnings))
        
    def _check_broad_permits(self) -> List[str]:
        """Detect unsafe broad permits (e.g. ALLOW ANY to INTERNAL)."""
        warnings = []
        for rule in self.rules:
            src = rule.get('source')
            dst = rule.get('destination')
            act = rule.get('action')
            
            if act == 'ALLOW' and src in ['ANY', 'EXTERNAL', '0.0.0.0/0']:
                if dst == 'INTERNAL' or self.zones.get(dst, dst) == self.zones.get('INTERNAL', ''):
                    warnings.append(f"Unsafe broad permit detected in rule: '{rule.get('name')}'. "
                                    f"Allows EXTERNAL to INTERNAL directly.")
        return warnings
