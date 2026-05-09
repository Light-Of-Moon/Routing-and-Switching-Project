import re

with open('templates/index.html', 'r') as f:
    text = f.read()

old_port_html = """                            <div style="flex:0.5; min-width: 80px;">
                                <label style="font-size:12px; color:var(--text-muted); display:block; margin-bottom:4px; font-weight:600;">Port</label>
                                <input type="number" id="rt-port" placeholder="80" class="b-input" value="80" style="width: 100%; border: 1px solid var(--panel-border);">
                            </div>"""

new_port_html = """                            <div style="flex:0.5; min-width: 80px;">
                                <label style="font-size:12px; color:var(--text-muted); display:block; margin-bottom:4px; font-weight:600;">Service/Port</label>
                                <select id="rt-port-select" class="b-input" style="width: 100%; border: 1px solid var(--panel-border);" onchange="if(this.value=='CUSTOM') { document.getElementById('rt-port-custom').style.display='block'; document.getElementById('rt-port').value=''; } else { document.getElementById('rt-port-custom').style.display='none'; document.getElementById('rt-port').value=this.value; }">
                                    <option value="80">HTTP (80)</option>
                                    <option value="443">HTTPS (443)</option>
                                    <option value="22">SSH (22)</option>
                                    <option value="3389">RDP (3389)</option>
                                    <option value="3306">MySQL (3306)</option>
                                    <option value="5432">PostgreSQL (5432)</option>
                                    <option value="CUSTOM">Custom Port</option>
                                </select>
                                <div id="rt-port-custom" style="display:none; margin-top:5px;">
                                    <input type="number" id="rt-port" placeholder="Port Num" class="b-input" value="80" style="width: 100%; border: 1px solid var(--panel-border);">
                                </div>
                            </div>"""

if old_port_html in text:
    with open('templates/index.html', 'w') as f:
        f.write(text.replace(old_port_html, new_port_html))
    print("HTML updated.")
else:
    print("Old port HTML not found.")
