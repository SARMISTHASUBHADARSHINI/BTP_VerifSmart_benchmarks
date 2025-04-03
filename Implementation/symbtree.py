import os
import json
from collections import defaultdict

from manticore.ethereum import ManticoreEVM
from z3 import *

class SymbolicExecutionTree:
    """Class to represent the symbolic execution tree."""

    class Node:
        def __init__(self, state_id, parent=None, condition=None):
            self.state_id = state_id
            self.parent = parent
            self.children = []
            self.condition = condition  # Condition leading to this node

        def add_child(self, child_node):
            self.children.append(child_node)

    def __init__(self):
        self.root = self.Node(state_id=0)
        self.nodes = {0: self.root}

    def add_node(self, state_id, parent_id, condition):
        parent_node = self.nodes.get(parent_id)
        if parent_node:
            new_node = self.Node(state_id, parent=parent_node, condition=condition)
            parent_node.add_child(new_node)
            self.nodes[state_id] = new_node
        else:
            raise ValueError(f"Parent node {parent_id} not found!")

    def get_root(self):
        return self.root


def compile_solidity_contract(solidity_file):
    """Compile Solidity contract and return bytecode."""
    os.system(f"solc --bin {solidity_file} -o compiled --overwrite")
    contract_name = os.path.splitext(os.path.basename(solidity_file))[0]
    bytecode_file = f"compiled/{contract_name}.bin"

    with open(bytecode_file, "r") as f:
        bytecode = f.read().strip()

    return bytecode


def run_symbolic_execution(bytecode):
    """Run symbolic execution on bytecode and construct execution tree."""
    m = ManticoreEVM()
    user_account = m.create_account(balance=1000)
    contract_account = m.create_contract(owner=user_account, init=bytecode)

    tree = SymbolicExecutionTree()
    state_map = {m.world.state.id: 0}  # Maps Manticore states to tree nodes

    for state_id in m.ready_states:
        constraints = m.world[state_id].constraints
        parent_id = state_map.get(state_id, 0)

        for constraint in constraints:
            tree.add_node(state_id, parent_id, str(constraint))

    return tree.get_root()


if __name__ == "__main__":
    solidity_file = "example.sol"  # Replace with your contract file
    bytecode = compile_solidity_contract(solidity_file)
    root_node = run_symbolic_execution(bytecode)

    print("Symbolic Execution Tree Root:", root_node)
