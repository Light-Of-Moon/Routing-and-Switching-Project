# Project Details

## Rule/Role Creation
Roles are mapped and created in the `policies/*.yaml` configuration file (e.g., `example_corporate.yaml`) under the `roles:` dictionary. Each role (e.g., `admin`, `guest`, `developer`) is given a logical name, a functional description, and mapped to specific physical or logical `source_zones`. For instance, the `admin` role maps to the `internal` and `vpn` zones.
When you create firewall rules, you list the logical `role` they apply to, making the policies far easier for humans to read and audit.

## Applying Roles and Rules
When you apply a rule (or modify policies linked to these roles) through the frontend, the Backend parses the YAML file. The `Compiler` resolves these logical roles and zones into specific network structures (IP subnets, protocol types, actions). The rules are translated into the equivalent compiled Linux `iptables` or `nftables` commands.
The dashboard directly passes the generated commands via the command line to be physically applied on the firewall. 

## Which Components or Services these Apply To
Rules are applied explicitly against `Services` (mapped globally to known destination ports, like `HTTP` = tcp:80, `SSH` = tcp:22) across predefined `Zones` (`internal`, `dmz`, `vpn`, and `external` subnets). This prevents certain network sectors from reaching unpermitted services in others (e.g., stopping external attackers from querying internal databases directly).

## Docker Infrastructure

The deployment relies on several containers managed via Docker Compose.

**1. The External Container (The Attacker/Outside Network)**
The container that officially acts as the internet/outside world natively in Docker is `zone_external` (assigned to 172.20.0.50). 

**2. Treating Your Local Machine as The External Side**
Docker networking bridges internal traffic on your host system. Because the Flask application `dashboard_app` operates securely bounded to the `host` network (or directly on your local system via Python environments running `python real_dashboard.py`), your local machine interacts with these networks directly. Testing endpoints into the firewall translates the Docker Gateway (`172.20.x.1`) as the external point of ingress.

**3. Are Rules Applied Directly to the Firewall Container?**
**Yes.** When a rule is compiled and dispatched from the Dashboard, the `.py` script runs `docker exec firewall iptables ...` under the hood. You are physically shifting network rules in the real-time routing environment of the `firewall` container instance without rebooting.

**4. Containers Behind the Firewall**
There are several zone hosts effectively trapped behind the core `firewall` container acting as their network gateway:
- **`zone_internal` (10.0.5.10):** Represents internal corporate hosts.
- **`zone_dmz` (192.168.50.10):** Represents your exposed outward-facing servers (running an active Nginx web server).
- **`zone_vpn` (10.8.0.10):** Simulates remote VPN users trying to dial into your network securely.

**5. Does Creating, Compiling and Applying It *Really* Apply It?**
**Yes.** The `subprocess.run(["docker", "exec", "firewall", ...])` actively forces the target container's kernel routing policies to conform to your new specification simultaneously as you press compile. 

**6. Verification and Confirmation**
To verify the rules sit exactly where they are supposed to be, you can:
- **Check Dashboard:** Inspect the "Device View" panel inside your dashboard as it renders live iptables dumps.
- **Via CLI:** Run `flatpak-spawn --host docker exec firewall iptables -L -n -v` (or just `docker exec ...` on standard machines) in your terminal to see raw bytes and packets hitting your configured tables.
- **Through the Policy Tester Tab:** Use the new "📡 Policy Tester (Live)" tab built right into the main dashboard page. Simply select your simulated testing parameters in the UI (e.g., `EXTERNAL` -> `DMZ`, Port `80`), hit "Run Connectivity Test", and the backend orchestrates isolated `nmap` Docker bounds checks simultaneously against the physical rules to show you definitively `ALLOW`, `DENY`, or `CLOSED`.

---

### Important Explanations for Testing Anomalies (Troubleshooting Guide)

**Why did my scan from my main Host Machine (outside the app) show the port as OPEN, even though the firewall Dropped it?**
Because of Docker's intrinsic bridge networking! When you run Native `nmap 192.168.50.10` from your Host OS, Docker bypasses the `firewall` container completely! Your Host utilizes the intrinsic IP route map (`dmz_net`) that allows it to talk directly to `zone_dmz` ignoring the simulated gateway. **You must exclusively perform port-testing from the `zone_external` container** (which is configured to strictly bounce its routing through `172.20.0.254` up into the firewall).

**Why did my rule say `action: DENY` or `action: allow`, yet compiled into the *opposite* `iptables` behavior in the Device Raw rules?**
This previously occurred because the Python backend explicitly checked for uppercase exact-matches (`== 'ALLOW'`). Thus, typing `allow` defaulting to DROP, and mistakenly evaluating variations. This strictly case-sensitive parsing bug has now been resolved to gracefully accept upper/lowercase formats dynamically in `compiler.py`.

**Why did the Device Rules Dashboard give a "127" Exit Status/Crash?**
"Exit status 127" meant that the `iptables` executable simply wasn't installed inside the `firewall` Docker container's Alpine environment, forcing the backend Python dashboard to crash when querying `iptables -S`. This has been permanently fixed by updating `docker-compose.yml` to automatically inject `apk add iptables` upon container initialization.

---

### Scenario: Rule Creation & Testing Workflow

**Goal:** Ensure a new firewall rule correctly controls traffic from external access (e.g., blocking HTTP to DMZ).

1. **Modify Policy:** Edit `policies/example_corporate.yaml`. Find the rule allowing HTTP to the DMZ (e.g., `RULE-030`) and change its `action: "allow"` to `action: "deny"`.
2. **Compile & Apply Rule:**
   - In the web dashboard (`http://127.0.0.1:5001`), select "Load Policy" using the edited `example_corporate.yaml`.
   - Review the compiled `iptables` commands.
   - Click **"Apply to Device"**. This securely proxies the rule out to the `firewall` Docker container using `subprocess` calls.
3. **Verify the Network Effect (The Test):**
   - **Test Tool:** Use the built-in "Run Attack Simulation" tool on the dashboard targeting the DMZ web server IP (`192.168.50.10`).
   - By default, it spawns `flatpak-spawn --host docker exec zone_external nmap ...` simulating an outside scan.
   - **Observation:** You should observe that `port 80` (HTTP) is now marked as `filtered` or fails to return a response from Nmap. This absolutely proves the `firewall` container is actively isolating the traffic.
4. **Device Rollback/Revert:**
   - Change `action: "allow"` back in the YAML. Unplug the drop rule by repeating the "Load Policy" -> "Apply to Device" process.
   - Run the Nmap scan again from the dashboard. Port `80/tcp` will now definitively say `open` with returning HTTP signatures.