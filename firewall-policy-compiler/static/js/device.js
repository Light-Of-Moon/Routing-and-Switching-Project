document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('btn-refresh');
    const executeBtn = document.getElementById('btn-execute-raw');
    const rawPre = document.getElementById('rules-output');
    const rulesTbody = document.getElementById('rules-tbody');
    const policiesContainer = document.getElementById('policies-container');
    const toast = document.getElementById('toast');

    function showToast(msg, isError = false) {
        toast.textContent = msg;
        toast.style.borderLeft = `4px solid ${isError ? 'var(--accent-danger)' : 'var(--accent-success)'}`;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    // Helper to extract action badge
    function getActionBadge(ruleText) {
        if (ruleText.includes('-j ACCEPT')) return '<span class="badge accept">ACCEPT</span>';
        if (ruleText.includes('-j DROP')) return '<span class="badge drop">DROP</span>';
        if (ruleText.includes('-j REJECT')) return '<span class="badge drop">REJECT</span>';
        if (ruleText.includes('-j LOG')) return '<span class="badge log">LOG</span>';
        if (ruleText.includes('-j MASQUERADE')) return '<span class="badge">MASQUERADE</span>';
        if (ruleText.includes('-j DNAT')) return '<span class="badge">DNAT</span>';
        if (ruleText.includes('-j SNAT')) return '<span class="badge">SNAT</span>';
        return '<span class="badge">OTHER</span>';
    }

    async function loadRulesJSON() {
        try {
            const res = await fetch('/device_rules_json');
            const data = await res.json();
            
            if (data.success) {
                // Render Policies
                policiesContainer.innerHTML = '';
                data.chains.forEach(c => {
                    const badgeClass = c.policy === 'ACCEPT' ? 'accept' : (c.policy === 'DROP' ? 'drop' : '');
                    policiesContainer.innerHTML += `
                        <span style="margin-right: 15px; font-size: 14px; color: var(--text-main);">
                            <strong>${c.chain} Default:</strong> 
                            <span class="badge ${badgeClass}">${c.policy}</span>
                        </span>
                    `;
                });

                // Render Rules
                if (data.rules.length === 0) {
                    rulesTbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 30px; color: var(--text-muted);">No rules found. Default policies apply.</td></tr>';
                } else {
                    rulesTbody.innerHTML = '';
                    data.rules.forEach(r => {
                        const tr = document.createElement('tr');
                        
                        tr.innerHTML = `
                            <td><strong>${r.chain}</strong></td>
                            <td style="color: var(--text-muted);">${r.rule_num}</td>
                            <td style="color: #a78bfa;">${r.rule.replace(/-j \w+/, '')}</td>
                            <td>${getActionBadge(r.rule)}</td>
                            <td>
                                <button class="edit-btn" data-cmd="${(r.edit_cmd || '').replace(/"/g, '&quot;')}">Edit</button>
                                <button class="delete-btn" data-cmd="${r.delete_cmd.replace(/"/g, '&quot;')}">Delete</button>
                            </td>
                        `;
                        rulesTbody.appendChild(tr);
                    });

                    // Attach edit listeners
                    document.querySelectorAll('.edit-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            const cmd = e.target.getAttribute('data-cmd');
                            const input = document.getElementById('raw-command');
                            input.value = cmd;
                            input.focus();
                            document.getElementById('btn-execute-raw').textContent = 'Save Edit';
                            showToast('Edit mode: Modify the command and hit Save', false);
                        });
                    });

                    // Attach delete listeners
                    document.querySelectorAll('.delete-btn').forEach(btn => {
                        btn.addEventListener('click', async (e) => {
                            const cmd = e.target.getAttribute('data-cmd');
                            if (confirm(`Are you sure you want to delete this rule?\n\n${cmd}`)) {
                                await executeCommand(cmd);
                            }
                        });
                    });
                }
            } else {
                rulesTbody.innerHTML = `<tr><td colspan="4" style="color: var(--accent-danger);">Error: ${data.error}</td></tr>`;
                showToast('Failed to load parsed rules', true);
            }
        } catch (err) {
            rulesTbody.innerHTML = `<tr><td colspan="4" style="color: var(--accent-danger);">Network Error</td></tr>`;
        }
    }

    async function loadRulesRaw() {
        rawPre.textContent = 'Fetching rules...';
        try {
            const res = await fetch('/device_rules');
            const data = await res.json();
            
            if (data.success) {
                rawPre.textContent = data.output || 'No rules configured.';
            } else {
                rawPre.textContent = `Error loading rules: ${data.error}`;
            }
        } catch (err) {
            rawPre.textContent = 'Network error while fetching rules.';
        }
    }

    async function loadAll() {
        await loadRulesJSON();
        await loadRulesRaw();
    }

    refreshBtn.addEventListener('click', loadAll);

    async function executeCommand(cmd) {
        try {
            const res = await fetch('/device_rule_action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'custom', command: cmd })
            });
            const data = await res.json();
            
            if (data.success) {
                showToast(data.message);
                loadAll();
            } else {
                showToast(`Error: ${data.error}`, true);
            }
        } catch (err) {
            showToast('Network error while executing.', true);
        }
    }

    executeBtn.addEventListener('click', async () => {
        const cmd = document.getElementById('raw-command').value;
        if (!cmd) return showToast('Please enter a command', true);
        
        executeBtn.textContent = 'Running...';
        await executeCommand(cmd);
        document.getElementById('raw-command').value = '';
        executeBtn.textContent = 'Add Rule';
    });

    // Initial load
    loadAll();
});
