with open('templates/index.html', 'r') as f:
    content = f.read()

old_test_harness = """                <!-- Test Results -->
                <div class="glass-panel test-card" id="test-card">
                    <div class="panel-header">
                        <h2>Test Harness</h2>
                    </div>
                    <div class="test-content" id="test-content">
                        <p class="placeholder-text">Run tests to see live connectivity results.</p>
                    </div>
                </div>"""

new_rule_tester = """                <!-- Rule Testing Tab / Panel -->
                <div class="glass-panel" id="rule-testing-card" style="border: 2px solid var(--accent-primary); box-shadow: 0 4px 15px rgba(0,200,255,0.1);">
                    <div class="panel-header" style="display:flex; justify-content: space-between; align-items:center;">
                        <h2 style="display: flex; align-items: center; gap: 8px;">📡 Policy Tester (Live)</h2>
                        <span class="status-badge" id="test-status-badge" style="background:var(--accent-secondary); padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;">Ready</span>
                    </div>
                    <div class="test-content" style="padding: 16px;">
                        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 15px;">Verify the actual effect of the firewall rule in real time by testing inter-container connectivity.</p>
                        <div style="display: flex; gap: 10px; margin-bottom: 12px; flex-wrap: wrap;">
                            <div style="flex:1; min-width: 120px;">
                                <label style="font-size:12px; color:var(--text-muted); display:block; margin-bottom:4px; font-weight:600;">Source Zone</label>
                                <select id="rt-source" class="b-input" style="width: 100%; border: 1px solid var(--panel-border);">
                                    <option value="EXTERNAL">EXTERNAL</option>
                                    <option value="INTERNAL">INTERNAL</option>
                                    <option value="VPN">VPN</option>
                                    <option value="DMZ">DMZ</option>
                                </select>
                            </div>
                            <div style="display:flex; align-items:flex-end; padding-bottom:8px; color: var(--text-muted);">
                                ➔
                            </div>
                            <div style="flex:1; min-width: 120px;">
                                <label style="font-size:12px; color:var(--text-muted); display:block; margin-bottom:4px; font-weight:600;">Destination Zone</label>
                                <select id="rt-dest" class="b-input" style="width: 100%; border: 1px solid var(--panel-border);">
                                    <option value="DMZ" selected>DMZ</option>
                                    <option value="INTERNAL">INTERNAL</option>
                                    <option value="EXTERNAL">EXTERNAL</option>
                                    <option value="VPN">VPN</option>
                                </select>
                            </div>
                            <div style="flex:0.5; min-width: 80px;">
                                <label style="font-size:12px; color:var(--text-muted); display:block; margin-bottom:4px; font-weight:600;">Port</label>
                                <input type="number" id="rt-port" placeholder="80" class="b-input" value="80" style="width: 100%; border: 1px solid var(--panel-border);">
                            </div>
                        </div>
                        <button id="btn-run-rule-test" class="btn primary" style="width: 100%; border-radius:6px; background-color: var(--accent-success); margin-top: 5px; font-weight:600; padding:10px;">⚡ Run Connectivity Test</button>
                        
                        <div id="rt-result-area" style="margin-top: 15px; display: none;">
                            <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom:8px;">
                                <strong style="font-size:14px;">Live Output:</strong>
                                <span id="rt-final-result" style="padding: 3px 8px; border-radius: 4px; font-size: 13px; font-family:var(--font-code); font-weight:bold;"></span>
                            </div>
                            <pre id="rt-output" class="code-block" style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px; overflow-x: auto; max-height: 200px; font-size:12px; white-space:pre-wrap; border: 1px solid var(--panel-border);"></pre>
                        </div>
                    </div>
                </div>"""

if old_test_harness in content:
    content = content.replace(old_test_harness, new_rule_tester)
    with open('templates/index.html', 'w') as f:
        f.write(content)
    print("HTML updated.")
else:
    print("Old test harness not found.")
