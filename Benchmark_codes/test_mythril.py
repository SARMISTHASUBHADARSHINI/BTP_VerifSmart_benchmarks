import os
import subprocess
import json
import argparse
import shutil

# Base path (Update if needed)
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(BASE_PATH, "results", "Mythril")
MYTHRIL_CMD = shutil.which("myth")  # Dynamically find Mythril path
TIMEOUT = 600000

# Updated bug categories from your structure
BUG_CATEGORIES = [
    "Overflow-Underflow", "Re-entrancy", "Timestamp-Dependency", "TOD",
    "tx.origin", "Unchecked-Send", "Unhandled-Exceptions"
]

def find_buggy_contracts():
    """Find all buggy contracts categorized by bug type."""
    buggy_contracts = {}
    buggy_contracts_dir = os.path.join(BASE_PATH, "buggy_contracts")

    for bug_type in BUG_CATEGORIES:
        bug_dir = os.path.join(buggy_contracts_dir, bug_type)
        if os.path.exists(bug_dir):
            contracts = [os.path.join(bug_dir, f) for f in os.listdir(bug_dir) if f.endswith(".sol")]
            buggy_contracts[bug_type] = contracts

    return buggy_contracts


def run_mythril(contract_path):
    """Run Mythril on a Solidity contract and return detected vulnerabilities."""
    
    if not MYTHRIL_CMD:
        return "Error: Mythril is not installed or not in PATH"

    try:
        print(f"🔍 Running Mythril on: {contract_path}")
        # result = subprocess.run(
        #     f"{MYTHRIL_CMD} analyze {contract_path} -o json",
        #     shell=True, capture_output=True, text=True
        # )
        print(f"python -m mythril analyze {contract_path} -o json")
        result = subprocess.run(
            f"python -m mythril analyze {contract_path} -o json",
            shell=True, capture_output=True, text=True
        )
    
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        return result.stdout.strip()
    
    except subprocess.TimeoutExpired:
        return "Error: Mythril execution timed out"
    
    except Exception as e:
        return f"Unexpected Error: {str(e)}"


def parse_mythril_output(output):
    """Extract detected vulnerabilities from Mythril JSON output."""
    detected_vulnerabilities = []
    try:
        output_json = json.loads(output)
        for issue in output_json.get("issues", []):
            detected_vulnerabilities.append(issue.get("title", "Unknown"))
    except json.JSONDecodeError:
        pass  # Handle non-JSON output (e.g., errors)
    return set(detected_vulnerabilities)


def test_mythril():
    """Run Mythril on all buggy contracts and validate its accuracy."""
    buggy_contracts = find_buggy_contracts()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    results = []

    for bug_type, contracts in buggy_contracts.items():
        print(f"\n🚀 Testing {len(contracts)} contracts with {bug_type} bugs...")

        for contract_path in contracts:
            contract_name = os.path.basename(contract_path)
            output = run_mythril(contract_path)
            detected_vulnerabilities = parse_mythril_output(output)

            result = {
                "contract": contract_name,
                "bug_type": bug_type,
                "path": contract_path,
                "detected_vulnerabilities": list(detected_vulnerabilities),
                "mythril_output": output
            }
            results.append(result)
            print(result)

            if detected_vulnerabilities:
                print(f"✅ Vulnerabilities detected in {contract_name}: {detected_vulnerabilities}")
            else:
                print(f"⚠️  No vulnerabilities detected in {contract_name}")

    # Save results for inspection
    results_file = os.path.join(RESULTS_DIR, "mythril_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=4)

    print(f"\n✅ Results saved to {results_file}")


if __name__ == "__main__":
    test_mythril()
