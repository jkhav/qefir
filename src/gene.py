import random
import numpy
from typing import List
from gate import Gate
import copy

class Gene:
    def __init__(self, gate : str = 'empty', target : int = -1, controls : List[int] = None, parameter : float = 0.0):
        self.gate = gate
        self.multiqubit_idx = 0 # to synchronize the parts of the multi-qubit gates, all parts of the same gate have the same index
        self.part = -1 # if part == -1, its single-qubit, otherwise it tells which part of the multi-qubit gate it is
        self.skips = 0
        self.active = True
        
    def random(self, gate_set=None, max_qubit : int = 2, parameter_range = (-numpy.pi, numpy.pi), max_skips : int = 0) -> Gate:
        gate = random.choice(gate_set)
        self.gate = gate.name
        self.skips = random.randint(0, max_skips)
        if gate.multi_qubit:
            self.part = random.randint(0, gate.qubits - 1)
            # index is initialized when placing it in the column
        return gate

    def print_gene(self):
        print(f"Gate: {self.gate}, Target: {self.target_qubit}")

    def __str__(self):
        return f"{self.gate} {self.part} {self.multiqubit_idx}"

    def copy(self):
        return copy.deepcopy(self)