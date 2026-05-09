# Firewall Policy Compiler & Dashboard

Welcome to the **Firewall Policy Compiler**, a comprehensive tool and web dashboard designed to translate human-readable YAML firewall configurations into raw `iptables` / `nftables` commands. The project simulates a fully functional corporate network within Docker and applies real-time policies across different network zones.

## Overview

For a deep dive into the system's architecture, including its handling of network zones (External, DMZ, Internal, VPN), rule translation, and Docker networking, refer to [PROJECT_DETAILS.md](PROJECT_DETAILS.md).

## How to Start the Project

Follow these steps to get the Firewall Policy Compiler up and running on your local machine:

**1. Start the Docker Infrastructure**
The project relies on Docker to simulate the network architecture (firewall, external, dmz, internal, and vpn zones).
```bash
docker compose up -d --build
```
*(If running from a sandboxed VS Code Flatpak on Linux, prefix the command with `flatpak-spawn --host`)*

**2. Setup the Python Backend**
Create and activate a virtual environment, then install the dependencies.
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run the Dashboard**
Start the main Flask application to serve the interactive web interface.
```bash
python real_dashboard.py
```

**4. Access the Frontend**
Open your web browser and navigate to: [http://127.0.0.1:5001](http://127.0.0.1:5001)

For more detailed troubleshooting or stopping the containers, please refer to [HOW_TO_RUN.md](HOW_TO_RUN.md).

## Project Structure & File Index

The following is an index of all files and directories in this repository, providing a clear map of the codebase components:

### Core Logic & Routing
* **`compiler.py`**: The core translation engine that compiles human-readable YAML configurations into raw `iptables` or `nftables` commands.
* **`policy_parser.py`**: Handles parsing and validation of the YAML configuration files to be processed by the compiler.
* **`auditor.py`**: Audits the compiled firewall rules for potential security risks, overlaps, or inefficiencies.
* **`attack_engine.py`**: Simulates scanning (using `nmap`) and other attacks against the Docker firewall instance to live-test rules.
* **`nat_dmz.py`**: Manages and compiles specific Network Address Translation (NAT) rules, especially for the DMZ routing.
* **`vpn_config.py`**: Handles generating configurations and firewall integration specifically for the simulated VPN network zone.
* **`rollback.py`**: Contains the logic necessary to revert or clear newly applied rules from the firewall dynamically.

### Web Dashboard (Frontend & Backend)
* **`real_dashboard.py`**: The primary Flask backend application serving the interactive dashboard. Translates frontend REST/UI requests to compiler actions.
* **`static/`**: Contains static assets like JavaScript logic and CSS styling for the interactive web frontend.
* **`templates/`**: Holds the HTML rendering templates for the Flask dashboard UI.
* **`package.json` / `package-lock.json`**: Node ecosystem files for tracking frontend package dependencies and utility scripts.
* **`requirements.txt`**: Standard Python dependency file listing necessary packages.

### Infrastructure & Orchestration
* **`docker-compose.yml`**: The Docker orchestration file defining the interconnected network topology (`firewall`, `zone_internal`, `zone_dmz`, `zone_vpn`, `zone_external`).
* **`Dockerfile`**: Defines the foundational base images for the containers used in the simulated network infrastructure.

### Scripts & Utilities
* **`patch_html.py`, `patch_html2.py`, `patch_js.py`, `patch_js2.py`, `patch_py.py`**: Utility scripts intended for updating, formatting, or live-patching backend logic and frontend templates.
* **`fix_dashboard.py`**: Script for executing environment or dashboard repairs/patches dynamically.
* **`run_attack.py`**: Execution wrapper to instantly fire off the `attack_engine` simulations.
* **`test_harness.py`**: The automated testing suite configured to run assertions on the backend logic and the compiler outputs.
* **`test-dom.js`, `test-html.js`**: Frontend testing definitions for dashboard interactive elements.

### Configuration Policies
* **`policies/`**: Directory containing user-defined YAML files. These act as the source code for your rules.

### Documentation
* **`HOW_TO_RUN.md`**: Guide for installing dependencies, starting Docker instances, and booting the UI.
* **`PROJECT_DETAILS.md`**: Deep dive into the architecture, zone mapping, and exact inner workings of rule enforcement.
