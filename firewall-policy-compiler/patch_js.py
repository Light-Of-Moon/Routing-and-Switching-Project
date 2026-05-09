with open('static/js/main.js', 'r') as f:
    content = f.read()

js_addition = """
    // --- Rule Testing / Connectivity Test ---
    const runRuleTestBtn = document.getElementById('btn-run-rule-test');
    if (runRuleTestBtn) {
        runRuleTestBtn.addEventListener('click', async () => {
            const source = document.getElementById('rt-source').value;
            const dest = document.getElementById('rt-dest').value;
            const port = document.getElementById('rt-port').value;
            
            const badge = document.getElementById('test-status-badge');
            const resultArea = document.getElementById('rt-result-area');
            const outputEl = document.getElementById('rt-output');
            const finalResult = document.getElementById('rt-final-result');
            
            if (!port) {
                showToast("Please specify a target port", "error");
                return;
            }
            if (source === dest) {
                showToast("Source and destination zones should be different for meaningful firewall tests.", "warning");
            }
            
            runRuleTestBtn.disabled = true;
            runRuleTestBtn.innerHTML = 'Testing Connectivity...';
            badge.innerText = 'Scanning...';
            badge.style.background = 'var(--accent-warning)';
            
            resultArea.style.display = 'block';
            outputEl.innerText = `Executing: nmap -Pn -p ${port} from ${source} to ${dest}...`;
            finalResult.innerText = '';
            
            try {
                const res = await fetch('/connectivity_test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source: source, destination: dest, port: port })
                });
                
                const data = await res.json();
                if (data.success) {
                    outputEl.innerText = data.output;
                    finalResult.innerText = "RESULT: " + data.status;
                    
                    if (data.status.includes('ALLOW')) {
                        finalResult.style.color = '#fff';
                        finalResult.style.backgroundColor = 'var(--accent-success)';
                        badge.style.background = 'var(--accent-success)';
                        badge.innerText = 'Allow';
                    } else if (data.status.includes('DENY')) {
                        finalResult.style.color = '#fff';
                        finalResult.style.backgroundColor = 'var(--accent-danger)';
                        badge.style.background = 'var(--accent-danger)';
                        badge.innerText = 'Deny';
                    } else {
                        finalResult.style.backgroundColor = 'var(--panel-border)';
                        badge.style.background = 'var(--panel-border)';
                        badge.innerText = 'Closed';
                    }
                    showToast("Test completed successfully!");
                } else {
                    outputEl.innerText = "Error: " + data.error;
                    badge.innerText = 'Failed';
                    badge.style.background = 'var(--accent-danger)';
                    showToast(data.error, "error");
                }
            } catch (err) {
                outputEl.innerText = "Fetch Exception: " + err;
                badge.innerText = 'Failed';
                badge.style.background = 'var(--accent-danger)';
                showToast("Network error trying to run test.", "error");
            } finally {
                runRuleTestBtn.disabled = false;
                runRuleTestBtn.innerHTML = '⚡ Run Connectivity Test';
            }
        });
    }
"""

if "btn-run-rule-test" not in content:
    content = content + "\n" + js_addition
    with open('static/js/main.js', 'w') as f:
        f.write(content)
    print("JS updated.")
else:
    print("JS already contains test logic.")
