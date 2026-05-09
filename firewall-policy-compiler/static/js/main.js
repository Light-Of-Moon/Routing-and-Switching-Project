document.addEventListener('DOMContentLoaded', () => {
    const editor = document.getElementById('policy-editor');
    const compileBtn = document.getElementById('btn-compile');
    const testBtn = document.getElementById('btn-test');
    const snapshotBtn = document.getElementById('btn-snapshot');
    const applyBtn = document.getElementById('btn-apply');
    const toast = document.getElementById('toast');

    // YAML History State
    let yamlHistory = [editor.value];
    
    function saveYamlState() {
        if (editor.value !== yamlHistory[yamlHistory.length - 1]) {
            yamlHistory.push(editor.value);
            if (yamlHistory.length > 50) yamlHistory.shift(); // Keep last 50 states
        }
    }

    // Save state when manual edits occur (debounced or on blur)
    editor.addEventListener('blur', saveYamlState);
    editor.addEventListener('keydown', (e) => {
        // Save state on Enter if changed since last save
        if (e.key === 'Enter') {
            saveYamlState();
        }
    });

    const btnUndo = document.getElementById('btn-undo');
    if (btnUndo) {
        btnUndo.addEventListener('click', () => {
            saveYamlState(); // push current state just in case before undoing
            
            if (yamlHistory.length > 1) {
                // The current visual state might be the top of the stack, so pop it
                if (editor.value === yamlHistory[yamlHistory.length - 1]) {
                    yamlHistory.pop();
                }
                
                const prevState = yamlHistory[yamlHistory.length - 1] || yamlHistory[0];
                editor.value = prevState;
                showToast('Undo successful. Reverted to previous YAML state.');
                systemLog("Editor", "UNDO", "Reverted YAML to previous state.");
            } else {
                showToast('Nothing left to undo.', true);
            }
        });
    }

    // Tab Switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.code-block').forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(tab.dataset.target).classList.add('active');
        });
    });

    function showToast(msg, isError = false) {
        toast.textContent = msg;
        toast.style.borderLeft = `4px solid ${isError ? 'var(--accent-danger)' : 'var(--accent-success)'}`;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    // Modal behavior for System Logs
    const modalLogs = document.getElementById('logs-modal');
    const btnLogs = document.getElementById('btn-logs');
    const btnCloseLogs = document.getElementById('btn-close-logs');
    
    if (btnLogs && modalLogs && btnCloseLogs) {
        btnLogs.addEventListener('click', async () => {
            modalLogs.style.display = 'flex';
            
            // Fetch logs immediately
            const tb = document.getElementById('logs-table-body');
            tb.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px;">Fetching logs...</td></tr>';
            
            try {
                const res = await fetch('/logs');
                const data = await res.json();
                tb.innerHTML = '';
                
                if (data.logs.length === 0) {
                    tb.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px;">No system events recorded yet.</td></tr>';
                } else {
                    data.logs.forEach(l => {
                        const tr = document.createElement('tr');
                        tr.style.borderBottom = '1px solid #222';
                        
                        let color = '#ccc';
                        if(l.action === 'ERROR') color = 'var(--accent-danger)';
                        else if(l.action === 'APPLY') color = 'var(--accent-primary)';
                        else if(l.action === 'TEST') color = 'var(--accent-warning)';
                        else if(l.action === 'ADD RULE') color = 'var(--accent-success)';
                        else if(l.action === 'VPN MOD') color = '#9932CC';
                        
                        tr.innerHTML = `
                            <td style="padding: 10px; color: #888;">${l.timestamp}</td>
                            <td style="padding: 10px;">${l.module}</td>
                            <td style="padding: 10px; color: ${color}; font-weight: bold;">[${l.action}]</td>
                            <td style="padding: 10px;">${l.details}</td>
                        `;
                        tb.appendChild(tr);
                    });
                }
            } catch(e) {
                tb.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color:red;">Failed to retrieve logs.</td></tr>';
            }
        });
        
        btnCloseLogs.addEventListener('click', () => {
            modalLogs.style.display = 'none';
        });
    }

    async function systemLog(module, action, details) {
        try {
            await fetch('/system_log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ module, action, details })
            });
        } catch(e) {}
    }

    compileBtn.addEventListener('click', async () => {
        compileBtn.textContent = 'Compiling...';
        compileBtn.style.opacity = '0.8';
        
        try {
            const res = await fetch('/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: editor.value })
            });
            const data = await res.json();
            
            if (data.success) {
                // Update Code blocks
                document.getElementById('iptables-out').textContent = data.iptables || '// No output';
                document.getElementById('nftables-out').textContent = data.nftables || '// No output';
                document.getElementById('nat-out').textContent = data.nat || '// No output';
                document.getElementById('vpn-out').textContent = data.vpn || '// No output';
                
                // Update Audit
                const auditDiv = document.getElementById('audit-content');
                const scoreDiv = document.getElementById('audit-score');
                scoreDiv.textContent = data.audit.score;
                
                if (data.audit.score < 50) {
                    scoreDiv.style.background = 'var(--accent-danger)';
                } else if (data.audit.score < 80) {
                    scoreDiv.style.background = 'var(--accent-warning)';
                } else {
                    scoreDiv.style.background = 'var(--accent-success)';
                }

                let auditHtml = '';
                const warnings = [...data.audit.shadowing, ...data.audit.broad_permits];
                if (warnings.length === 0) {
                    auditHtml = '<p style="color: var(--accent-success)">✅ No issues found. Policy looks secure.</p>';
                } else {
                    warnings.forEach(w => {
                        auditHtml += `<div class="audit-item">⚠️ ${w}</div>`;
                    });
                }
                auditDiv.innerHTML = auditHtml;
                
                showToast('Compilation successful');
                systemLog("Compiler", "COMPILE", "Policy YAML compiled and audited successfully.");
            } else {
                showToast(`Error: ${data.error}`, true);
                systemLog("Compiler", "ERROR", `Policy compilation failed: ${data.error}`);
            }
        } catch (err) {
            showToast('Network error', true);
        } finally {
            compileBtn.textContent = 'Compile Policy';
            compileBtn.style.opacity = '1';
        }
    });

    if (testBtn) {
        testBtn.addEventListener('click', async () => {
            const testContent = document.getElementById('test-content');
            testContent.innerHTML = '<p class="placeholder-text">Executing real network checks against device...</p>';
        
        try {
            const res = await fetch('/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: editor.value })
            });
            const data = await res.json();
            
            if (data.success) {
                let html = '';
                data.results.forEach(t => {
                    const statusColor = t.status === 'PASS' ? 'var(--accent-success)' : 'var(--accent-danger)';
                    const statusBg = t.status === 'PASS' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';
                    
                    html += `
                        <div class="test-row" style="flex-direction: column; align-items: stretch; gap: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                <div>
                                    <div class="test-name">${t.name}</div>
                                    <div class="test-cmd" style="color: var(--accent-primary);">> ${t.command}</div>
                                    <div style="font-size: 12px; margin-top: 4px; color: var(--text-muted);">
                                        <strong>Expected:</strong> ${t.expected} | <strong>Actual:</strong> ${t.actual}
                                    </div>
                                </div>
                                <div class="test-status" style="background: ${statusBg}; color: ${statusColor};">${t.status}</div>
                            </div>
                            <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px;">
                                <strong style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Raw Terminal Output:</strong>
                                <pre style="margin-top: 5px; font-family: var(--font-code); font-size: 12px; color: #e2e8f0; white-space: pre-wrap; word-break: break-all;">${t.output || 'No output recorded.'}</pre>
                            </div>
                        </div>
                    `;
                });
                testContent.innerHTML = html;
                showToast('Tests completed');
                systemLog("Harness", "TEST SUITE", "Unit tests executed successfully against compiled rules.");
            } else {
                showToast(`Error: ${data.error}`, true);
                systemLog("Harness", "ERROR", `Unit tests failed: ${data.error}`);
                testContent.innerHTML = `<p class="placeholder-text">Test failed: ${data.error}</p>`;
            }
        } catch (err) {
            showToast('Network error', true);
        }
    });
    }

    snapshotBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('/snapshot', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Snapshot taken successfully');
                systemLog("Manager", "SNAPSHOT", "Firewall rules state snapshot saved successfully.");
            }
        } catch (err) {
            showToast('Failed to take snapshot', true);
            systemLog("Manager", "ERROR", "Failed to take snapshot due to network error.");
        }
    });
    
    // Allow tab key in editor
    editor.addEventListener('keydown', function(e) {
        if (e.key == 'Tab') {
            e.preventDefault();
            var start = this.selectionStart;
            var end = this.selectionEnd;
            this.value = this.value.substring(0, start) +
                "  " + this.value.substring(end);
            this.selectionStart =
                this.selectionEnd = start + 2;
        }
    });

    // Toggle Visual Builder
    document.getElementById('btn-toggle-builder').addEventListener('click', () => {
        const builder = document.getElementById('visual-builder');
        if (builder.style.display === 'none') {
            builder.style.display = 'flex';
        } else {
            builder.style.display = 'none';
        }
    });

    // Add Rule from Builder
    document.getElementById('btn-add-rule').addEventListener('click', () => {
        saveYamlState(); // Ensure the current state is stored before applying changes
        
        const name = document.getElementById('b-name').value || 'Visual Rule';
        const src = document.getElementById('b-source').value;
        const dst = document.getElementById('b-dest').value;
        let svc = document.getElementById('b-service').value;
        const act = document.getElementById('b-action').value;
        
        if (svc === 'CUSTOM') {
            svc = document.getElementById('b-custom-port').value || '8080';
        }
        
        let newRule = `  - name: "${name}"\n    source: ${src}\n    destination: ${dst}\n`;
        if (svc !== 'ANY') {
            newRule += `    service: ["${svc}"]\n`;
        }
        newRule += `    action: ${act}\n`;
        
        const lines = editor.value.split('\n');
        let rulesIndex = -1;
        let nextSectionIndex = -1;
        
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].startsWith('rules:')) {
                rulesIndex = i;
            } else if (rulesIndex !== -1 && lines[i].match(/^[a-zA-Z0-9_-]+:/)) {
                nextSectionIndex = i;
                break;
            }
        }
        
        if (rulesIndex === -1) {
            editor.value += '\nrules:\n' + newRule;
        } else if (nextSectionIndex === -1) {
            editor.value += '\n' + newRule;
        } else {
            lines.splice(nextSectionIndex, 0, newRule);
            editor.value = lines.join('\n');
        }
        
        showToast('Rule added to YAML');
        systemLog("Editor", "ADD RULE", "Appended a new rule snippet into the Policy YAML.");
    });

    // Apply to Device
    applyBtn.addEventListener('click', async () => {
        saveYamlState(); // track state when explicitly applying
        if (!confirm("WARNING: This will apply actual firewall rules to this device. Are you sure?")) return;
        
        applyBtn.textContent = 'Applying...';
        try {
            const res = await fetch('/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: editor.value })
            });
            const data = await res.json();
            
            if (data.success) {
                showToast(data.message);
                console.log(data.commands);
            } else {
                showToast(`Failed: ${data.error}`, true);
            }
        } catch (err) {
            showToast('Network error while applying', true);
        } finally {
            applyBtn.textContent = 'Apply to Device';
        }
    });

    // Attack Simulation Controller
    document.getElementById('btn-launch-sim').addEventListener('click', () => {
        const target = document.getElementById('sim-target').value;
        const scenario = document.getElementById('sim-scenario').value;
        
        const outPre = document.getElementById('sim-terminal');
        const countAllowed = document.getElementById('sim-allowed-count');
        const countBlocked = document.getElementById('sim-blocked-count');
        const countLogged = document.getElementById('sim-logged-count');
        
        outPre.textContent = 'Initializing Advanced Attack Simulation Framework...\n';
        countAllowed.textContent = '0';
        countBlocked.textContent = '0';
        countLogged.textContent = '0';
        
        const btn = document.getElementById('btn-launch-sim');
        btn.disabled = true;
        btn.textContent = 'SIMULATION IN PROGRESS...';
        btn.style.opacity = '0.7';
        document.getElementById('sim-status').outerHTML = '<span class="status-badge" id="sim-status" style="background:var(--accent-danger); color:#fff; font-size:12px;">Active</span>';
        
        let allowed = 0;
        let blocked = 0;
        let logged = 0;

        const eventSource = new EventSource(`/attack_stream?target=${encodeURIComponent(target)}&scenario=${encodeURIComponent(scenario)}`);
        
        eventSource.onmessage = function(event) {
            if (event.data === '[ATTACK_COMPLETE]') {
                eventSource.close();
                btn.disabled = false;
                btn.textContent = 'LAUNCH ATTACK SIMULATION';
                btn.style.opacity = '1';
                document.getElementById('sim-status').outerHTML = '<span class="status-badge" id="sim-status" style="background:var(--accent-success); color:#fff; font-size:12px;">Completed</span>';
                showToast('Simulation Execution Complete');                systemLog("Simulator", "ATTACK SIM", `Attack simulation module check finished on target ${target}`);                return;
            }
            
            // Parse custom telemetry from backend if available
            if (event.data.startsWith('[TELEMETRY]')) {
                const parts = event.data.substring(11).split('|');
                if (parts[0] === 'ALLOW') { allowed += parseInt(parts[1]); countAllowed.textContent = allowed; }
                if (parts[0] === 'BLOCK') { blocked += parseInt(parts[1]); countBlocked.textContent = blocked; }
                if (parts[0] === 'LOG') { logged += parseInt(parts[1]); countLogged.textContent = logged; }
                return; // don't print telemetry metadata to console
            }

            outPre.textContent += event.data + '\n';
            outPre.scrollTop = outPre.scrollHeight;
        };
        
        eventSource.onerror = function(err) {
            eventSource.close();
            btn.disabled = false;
            btn.textContent = 'LAUNCH ATTACK SIMULATION';
            btn.style.opacity = '1';
            document.getElementById('sim-status').outerHTML = '<span class="status-badge" id="sim-status" style="background:#555; color:#fff; font-size:12px;">Error</span>';
            outPre.textContent += '\n[Stream Connection Closed or Errored]\n';
        };
    });

    // Fetch Interfaces on Load
    async function loadInterfaces() {
        try {
            const res = await fetch('/interfaces');
            const data = await res.json();
            if (data.success) {
                document.getElementById('interface-list').textContent = data.interfaces.join(', ');
            } else {
                document.getElementById('interface-list').textContent = `Error: ${data.error}`;
            }
        } catch (err) {
            document.getElementById('interface-list').textContent = 'Failed to load interfaces.';
        }
    }
    
    loadInterfaces();
});


    // --- Rule Testing / Connectivity Test ---
    const runRuleTestBtn = document.getElementById('btn-run-rule-test');
    if (runRuleTestBtn) {
        runRuleTestBtn.addEventListener('click', async () => {
            const source = document.getElementById('rt-source').value;
            const dest = document.getElementById('rt-dest').value;
            const port = document.getElementById('rt-port-select').value === 'CUSTOM' ? document.getElementById('rt-port').value : document.getElementById('rt-port-select').value;
            
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

    // VPN Simulator Actions
    const btnVpnPush = document.getElementById('btn-push-vpn-rule');
    if(btnVpnPush) {
        btnVpnPush.addEventListener('click', async () => {
            const target = document.getElementById('vpn-acl-target').value;
            const port = document.getElementById('vpn-acl-port').value;
            const action = document.getElementById('vpn-acl-action').value;
            const outPre = document.getElementById('vpn-terminal');
            
            btnVpnPush.disabled = true;
            btnVpnPush.textContent = 'Pushing...';
            
            try {
                const res = await fetch('/vpn_rule_action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target, port, action })
                });
                const data = await res.json();
                
                outPre.textContent += `\n> [RULE PUSH] ${action} ${target} on Port ${port}\n`;
                if(data.success) {
                    outPre.textContent += `[Success] ${data.message}\n`;
                    showToast('VPN Rule successfully applied to firewall.');
                    systemLog("VPN Client", "VPN MOD", `Pushed interactive rule: ${action} ${target} on Port ${port}`);
                    const fb = document.getElementById('vpn-push-feedback');
                    if(fb) {
                        fb.style.display = 'inline-block';
                        fb.style.opacity = '1';
                        setTimeout(() => { fb.style.opacity = '0'; setTimeout(()=>fb.style.display='none',300); }, 3500);
                    }
                } else {
                    outPre.textContent += `[Error] ${data.error}\n`;
                    showToast('Error applying VPN rule', true);
                    systemLog("VPN Client", "ERROR", `Pushing VPN rule failed: ${data.error}`);
                }
            } catch(e) {
                outPre.textContent += `\n[Fatal] Network error pushing rule.\n`;
            }
            outPre.scrollTop = outPre.scrollHeight;
            btnVpnPush.disabled = false;
            btnVpnPush.textContent = 'Push Tunnel Rule → Firewall';
        });
    }

    const btnVpnTest = document.getElementById('btn-run-vpn-test');
    if(btnVpnTest) {
        btnVpnTest.addEventListener('click', () => {
            const target = document.getElementById('vpn-test-target').value;
            const type = document.getElementById('vpn-test-type').value;
            const outPre = document.getElementById('vpn-terminal');
            const resultBadge = document.getElementById('vpn-test-result');
            
            btnVpnTest.disabled = true;
            btnVpnTest.textContent = 'Executing...';
            btnVpnTest.style.opacity = '0.7';
            
            if(resultBadge) {
                resultBadge.textContent = 'TESTING...';
                resultBadge.style.background = '#333';
                resultBadge.style.color = '#fff';
            }
            
            outPre.textContent += `\n> [VPN TEST] Executing ${type} against ${target}...\n`;
            
            const eventSource = new EventSource(`/vpn_simulate_stream?target=${encodeURIComponent(target)}&type=${encodeURIComponent(type)}`);
            
            eventSource.onmessage = function(event) {
                if (event.data === '[TEST_COMPLETE]') {
                    eventSource.close();
                    btnVpnTest.disabled = false;
                    btnVpnTest.style.opacity = '1';
                    btnVpnTest.textContent = 'Execute Access Test';
                    return;
                }
                
                if (event.data.startsWith('[RESULT]')) {
                    if(!resultBadge) return;
                    const resType = event.data.split('|')[1];
                    if(resType === 'ALLOW') {
                        resultBadge.textContent = 'SUCCESS (ALLOWED)';
                        resultBadge.style.background = 'var(--accent-success)';
                        resultBadge.style.color = '#000';
                    } else {
                        resultBadge.textContent = 'FAILED (BLOCKED)';
                        resultBadge.style.background = 'var(--accent-danger)';
                        resultBadge.style.color = '#fff';
                    }
                    return;
                }

                outPre.textContent += event.data + '\n';
                outPre.scrollTop = outPre.scrollHeight;
            };
            
            eventSource.onerror = function() {
                eventSource.close();
                btnVpnTest.disabled = false;
                btnVpnTest.style.opacity = '1';
                btnVpnTest.textContent = 'Execute Access Test';
                outPre.textContent += '[Error/Closed Stream]\n';
            };
        });
    }
