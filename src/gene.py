import random
import numpy
from typing import List
from gate import Gate
import copy

class Gene:
    def __init__(self):
        self.gate = 'empty'
        self.parts = [] # List[int] qubit indices, first is target, rest are controls, size is fix by max_qubits_needed
        self.skips = 0
        self.active = True
        
    def random(self, gate_set : List[Gate], max_qubit : int, max_qubits_needed : int, max_skips : int) -> Gate:
        gate = random.choice(gate_set)
        self.gate = gate.name
        self.skips = random.randint(0, max_skips)
        self.parts = random.sample(range(max_qubit), max_qubits_needed)
        return gate

    def print_gene(self):
        print(f"Gate: {self.gate}, Parts: {self.parts}")

    def __str__(self):
        return f"{self.gate} {self.parts} {self.skips} {self.active}"

    def copy(self):
        return copy.deepcopy(self)