import solcx
import networkx as nx
import matplotlib.pyplot as plt
from pyevmasm import disassemble_all

# Install and set Solidity compiler version
solcx.install_solc("0.8.20")
solcx.set_solc_version("0.8.20")

def compile_solidity(source_code):
    """Compiles Solidity code and returns bytecode"""
    compiled_sol = solcx.compile_source(source_code, output_values=["bin"])
    contract_name = list(compiled_sol.keys())[0]  # Extract contract key
    bytecode = compiled_sol[contract_name]["bin"]
    print(bytecode)
    return bytecode

def extract_cfg(bytecode):
    """Extracts basic blocks and constructs a Control Flow Graph (CFG)"""
    instructions = disassemble_all(bytecode)
    cfg = {}
    edges = []
    current_block = []
    block_id = 0
    last_block = None

    for instr in instructions:
        current_block.append(instr)

        if instr.name.startswith("JUMP") or instr.name.startswith("JUMPI") or instr.name.startswith("STOP") or instr.name.startswith("RETURN"):
            cfg[block_id] = current_block
            if last_block is not None:
                edges.append((last_block, block_id))  # Connect last block to this one
            last_block = block_id
            block_id += 1
            current_block = []

    if current_block:
        cfg[block_id] = current_block

    return cfg, edges

def visualize_cfg(cfg, edges, filename="cfg.png"):
    """Visualizes the CFG and saves as an image (for GitHub Codespaces)"""
    G = nx.DiGraph()

    # Add nodes
    for block_id in cfg.keys():
        G.add_node(block_id, label=f"Block {block_id}")

    # Add edges
    for edge in edges:
        G.add_edge(*edge)

    # Draw the graph
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2000, font_size=10, font_weight="bold")
    labels = {node: f"B{node}" for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, font_color="black")

    plt.title("Control Flow Graph (CFG)")

    # Save graph as an image
    plt.savefig(filename)
    print(f"✅ CFG saved as {filename}. Saved")

# Call function with filename


# Example Solidity Code (Replace with any Solidity contract)
solidity_code = """
pragma solidity ^0.8.0;

contract Example {
    uint private balance;

    function deposit(uint amount) public {
        balance += amount;
    }

    function withdraw(uint amount) public {
        require(balance >= amount, "Insufficient balance");
        balance -= amount;
    }

    function getBalance() public view returns (uint) {
        return balance;
    }
}
"""

# Compile Solidity, extract CFG, and visualize
bytecode = compile_solidity(solidity_code)
cfg, edges = extract_cfg(bytecode)
# print(cfg)
visualize_cfg(cfg, edges, filename="cfg.png")

# ----------------------------------------------------------------------------------------

def extract_storage_accesses(cfg):
    storage_accesses = {}  # { function_id: { read: set(), write: set() } }
    
    for block_id, instructions in cfg.items():
        for instr in instructions:
            if instr.name == "SLOAD":
                storage_accesses.setdefault(block_id, {"read": set(), "write": set()})
                storage_accesses[block_id]["read"].add(instr.operand)
            elif instr.name == "SSTORE":
                storage_accesses.setdefault(block_id, {"read": set(), "write": set()})
                storage_accesses[block_id]["write"].add(instr.operand)

    return storage_accesses

storage_accesses = extract_storage_accesses(cfg)
print(storage_accesses)



