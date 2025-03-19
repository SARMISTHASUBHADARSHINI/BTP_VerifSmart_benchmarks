import os
import subprocess
import json
import argparse

# Paths (UPDATE THESE)
SOLIDIFI_PATH = "/path/to/solidiFI-benchmark"
VERIFSMART_CMD = "/path/to/verifsmart"

# Timeout for VerifSmart execution (in seconds)
TIMEOUT = 60

# Output directory for VerifSmart results
RESULTS_DIR = os.path.join(SOLIDIFI_PATH, "results", "VerifSmart")

# Ground truth: Injection logs are inside each bug type folder
BUG_CATEGORIES = ["Re-entrancy", "Timestamp", "UnhandledExceptions", 
                  "UncheckedSend", "TOD", "IntegerBugs", "TxOrigin"]

def find_buggy_contracts():
    """Find all buggy contracts categorized by bug type."""
    buggy_contracts = {}
    buggy_contracts_dir = os.path.join(SOLIDIFI_PATH, "buggy_contracts")

    for bug_type in BUG_CATEGORIES:
        bug_dir = os.path.join(buggy_contracts_dir, bug_type)
        if os.path.exists(bug_dir):
            contracts = [os.path.join(bug_dir, f) for f in os.listdir(bug_dir) if f.endswith(".sol")]
            buggy_contracts[bug_type] = contracts

    return buggy_contracts

def extract_injected_bugs(log_file):
    """Extract injected vulnerabilities from SolidiFI's bug log."""
    injected_bugs = []
    if not os.path.exists(log_file):
        return injected_bugs

    with open(log_file, "r") as f:
        for line in f:
            if "Bug Type:" in line:
                injected_bugs.append(line.split(":")[-1].strip())

    return set(injected_bugs)

def run_verifsmart(contract_path):
    """Run VerifSmart on a Solidity contract and return detected vulnerabilities."""
    try:
        result = subprocess.run(
            [VERIFSMART_CMD, contract_path], capture_output=True, text=True, timeout=TIMEOUT
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"

def parse_verifsmart_output(output):
    """Extract detected vulnerabilities from VerifSmart output."""
    detected_vulnerabilities = []
    for line in output.split("\n"):
        if "Detected vulnerability:" in line:
            detected_vulnerabilities.append(line.split(":")[-1].strip())
    return set(detected_vulnerabilities)

def test_verifsmart():
    """Run VerifSmart on all buggy contracts and validate its accuracy."""
    buggy_contracts = find_buggy_contracts()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    results = []

    for bug_type, contracts in buggy_contracts.items():
        print(f"\nTesting {len(contracts)} contracts with {bug_type} bugs...")

        for contract_path in contracts:
            contract_name = os.path.basename(contract_path)
            log_file = contract_path.replace(".sol", "_BugLog.txt")

            expected_vulnerabilities = extract_injected_bugs(log_file)
            output = run_verifsmart(contract_path)
            detected_vulnerabilities = parse_verifsmart_output(output)

            missed = expected_vulnerabilities - detected_vulnerabilities
            extra = detected_vulnerabilities - expected_vulnerabilities

            result = {
                "contract": contract_name,
                "bug_type": bug_type,
                "path": contract_path,
                "expected_vulnerabilities": list(expected_vulnerabilities),
                "detected_vulnerabilities": list(detected_vulnerabilities),
                "missed_vulnerabilities": list(missed),
                "extra_vulnerabilities": list(extra),
                "verifsmart_output": output
            }
            results.append(result)

            if missed:
                print(f"⚠️  Missed vulnerabilities in {contract_name}: {missed}")
            if extra:
                print(f"⚠️  False positives in {contract_name}: {extra}")

    # Save results for inspection
    results_file = os.path.join(RESULTS_DIR, "verifsmart_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=4)

    print(f"\n✅ Results saved to {results_file}")

if __name__ == "__main__":
    test_verifsmart()
