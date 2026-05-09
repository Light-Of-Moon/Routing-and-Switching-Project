# Firewall Policy Compiler - Complete Run Guide

This project is a comprehensive Firewall Policy Compiler & Dashboard that allows you to translate human-readable YAML configurations into raw `iptables` / `nftables` commands. These commands are visually audited by a backend and safely physically applied real-time onto an isolated array of Docker containers representing a fully functional corporate network (External, DMZ, Internal, VPN, and Firewall).

This guide details exactly how to deploy the entire stack from scratch.

---

## 🏗️ 1. Prerequisites

Ensure your system has the following dependencies installed natively:
- **Python 3.8+**
- **Docker** & **Docker Compose**
- *(If running from a sandboxed VS Code Flatpak on Linux): Ensure `flatpak-spawn` is available so commands proxy to the host.*

---

## 🐳 2. Start the Virtual Network & Containers

The project relies on a virtualized web of interconnected Docker networks that physically enforce the rules created by the policy compiler. Let's boot them up.

1. Open your terminal and navigate to the project directory:
   ```bash
   cd "firewall-policy-compiler"
   ```

2. Build and start the Docker Environment in detached mode:
   ```bash
   docker compose up -d --build
   ```
   *(If prompted inside a Flatpak IDE terminal like VS Code on Linux, prefix with `flatpak-spawn --host`:)*
   ```bash
   flatpak-spawn --host docker compose up -d --build
   ```

**What this achieves:**
Instantly creates 5 running containers mimicking physical hardware:
- **`firewall`**: The gateway node actively running `iptables` and filtering traffic natively.
- **`zone_internal`** (10.0.5.10): The corporate internal host.
- **`zone_dmz`** (192.168.50.10): The DMZ serving Nginx (`HTTP 80`).
- **`zone_vpn`** (10.8.0.10): Secure remote hosts.
- **`zone_external`** (172.20.0.50): The mock attacker outside the firewall.

---

## 🐍 3. Setup the Python Backend Environment

The Flask Dashboard runs locally on your machine and communicates with the Firewall container via Docker commands dynamically. We must install its dependencies.

1. While still inside `/firewall-policy-compiler`, create a Python Virtual Environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   - **Linux/Mac:** `source venv/bin/activate`
   - **Windows:** `venv\Scripts\activate`

3. Install the required Python packages (Flask, PyYAML, Rich, and others):
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 4. Run the Dashboard / Backend Service

Once your environment is active, you can boot the live web server interface.

1. Start the Flask Dashboard exactly like this:
   ```bash
   python real_dashboard.py
   ```
2. You will see output similar to:
   ```text
   * Serving Flask app 'real_dashboard'
   * Running on http://127.0.0.1:5001
   * Restarting with stat
   ```

---

## 💻 5. Accessing and Testing the Frontend Interface

1. **Open the App:** Open your web browser and navigate directly to:
   [http://127.0.0.1:5001](http://127.0.0.1:5001)

2. **Visual Rule Configuration:** 
   - Toggle the **"Toggle Visual Builder"** tab.
   - Use the dropdowns to draft a rule (e.g., `EXTERNAL` -> `DMZ` on `SSH (22)` -> `ALLOW`).
   - Hit **"Add Rule to Policy"**. This immediately structures and formats the YAML file perfectly for you.

3. **Compiler and Application Phase:**
   - Click the green **"Compile Policy"** button out at the top of the interface. The dashboard translates the YAML onto raw compiler tabs (`iptables`, `nat`).
   - Click the red **"Apply to Device"** button. This safely dispatches Python Subprocess pipelines that send the `iptables` string commands directly into the `firewall` Docker container routing kernel.

4. **Verify Application:**
   - Head over to the **"📡 Policy Tester (Live)"** tab.
   - Pick `EXTERNAL` as your source and `DMZ` as destination on target Port `22` (or `80`).
   - Hit **"⚡ Run Connectivity Test"**.
   - Your frontend dynamically requests the backend to spawn a real `nmap` container mapping check that respects the live firewall rules! You will immediately observe `ALLOW (Port Closed/Open)` or `DENY (Blocked/Filtered)`.

---

## 🛑 How to Shut Everything Down Safely
When you are done testing your firewall compilation structures:

1. Stop the Flask server by pressing `CTRL + C` in your currently running host terminal.
2. Deactivate the specific virtual environment:
   ```bash
   deactivate
   ```
3. Destroy the entire interconnected container layout gently by stopping Docker Compose:
   ```bash
   docker compose down
   ```
   *(Or with `flatpak-spawn --host docker compose down` where applicable).*
