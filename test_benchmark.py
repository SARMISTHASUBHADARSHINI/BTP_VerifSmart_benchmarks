import os
import subprocess
import json
import argparse

# Automatically detect the repository root
SOLIDIFI_PATH = os.path.dirname(os.path.abspath(__file__))
VERIFSMART_CMD = "/path/to/verifsmart"  # Update if needed

# Timeout for VerifSmart execution (in seconds)
TIMEOUT = 60

# Output directory for VerifSmart results
RESULTS_DIR = os.path.join(SOLIDIFI_PATH, "results", "VerifSmart")

# Updated categories based on provided directory structure
BUG_CATEGORIES = [
    "Overflow-Underflow", "Re-entrancy", "Timestamp-Dependency", "TOD",
    "tx.origin", "Unchecked-Send", "Unhandled-Exceptions"
]

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
        i = 0
        for contract_path in contracts:
            i= i+1
            contract_name = os.path.basename(contract_path)
            # print(contract_name)
            # print(i)
            output = run_verifsmart(contract_path)
        #     detected_vulnerabilities = parse_verifsmart_output(output)

        #     result = {
        #         "contract": contract_name,
        #         "bug_type": bug_type,
        #         "path": contract_path,
        #         "detected_vulnerabilities": list(detected_vulnerabilities),
        #         "verifsmart_output": output
        #     }
        #     results.append(result)

    # Save results for inspection
    results_file = os.path.join(RESULTS_DIR, "verifsmart_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=4)

    print(f"\n✅ Results saved to {results_file}")

if __name__ == "__main__":
    test_verifsmart()