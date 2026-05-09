import re

with open('static/js/main.js', 'r') as f:
    text = f.read()

old_add_rule = """    document.getElementById('btn-add-rule').addEventListener('click', () => {
        const name = document.getElementById('b-name').value || 'Visual Rule';
        const src = document.getElementById('b-source').value;
        const dst = document.getElementById('b-dest').value;
        let svc = document.getElementById('b-service').value;
        const act = document.getElementById('b-action').value;
        
        if (svc === 'CUSTOM') {
            svc = document.getElementById('b-custom-port').value || '8080';
        }
        
        let newRule = `\\n  - name: "${name}"\\n    source: ${src}\\n    destination: ${dst}\\n`;
        if (svc !== 'ANY') {
            newRule += `    service: ["${svc}"]\\n`;
        }
        newRule += `    action: ${act}\\n`;
        
        editor.value += newRule;
        showToast('Rule added to YAML');
    });"""

new_add_rule = """    document.getElementById('btn-add-rule').addEventListener('click', () => {
        const name = document.getElementById('b-name').value || 'Visual Rule';
        const src = document.getElementById('b-source').value;
        const dst = document.getElementById('b-dest').value;
        let svc = document.getElementById('b-service').value;
        const act = document.getElementById('b-action').value;
        
        if (svc === 'CUSTOM') {
            svc = document.getElementById('b-custom-port').value || '8080';
        }
        
        let newRule = `  - name: "${name}"\\n    source: ${src}\\n    destination: ${dst}\\n`;
        if (svc !== 'ANY') {
            newRule += `    service: ["${svc}"]\\n`;
        }
        newRule += `    action: ${act}\\n`;
        
        const lines = editor.value.split('\\n');
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
            editor.value += '\\nrules:\\n' + newRule;
        } else if (nextSectionIndex === -1) {
            editor.value += '\\n' + newRule;
        } else {
            lines.splice(nextSectionIndex, 0, newRule);
            editor.value = lines.join('\\n');
        }
        
        showToast('Rule added to YAML');
    });"""

if old_add_rule in text:
    text = text.replace(old_add_rule, new_add_rule)
    # also update the rt-port logic
    text = text.replace("const port = document.getElementById('rt-port').value;", "const port = document.getElementById('rt-port-select').value === 'CUSTOM' ? document.getElementById('rt-port').value : document.getElementById('rt-port-select').value;")
    with open('static/js/main.js', 'w') as f:
        f.write(text)
    print("JS updated.")
else:
    print("Old Add Rule not found.")
