import sys
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit_sliqsim_provider import SliQSimProvider
import evolution as evo
from genome import Genome
from gene import Gene

if __name__ == "__main__":
    
    hadamard = evo.Gate(name='h', qubits=1, parameter=0.0)
    x = evo.Gate(name='x', qubits=1, parameter=0.0)
    y = evo.Gate(name='y', qubits=1, parameter=0.0)
    z = evo.Gate(name='z', qubits=1, parameter=0.0)
    s = evo.Gate(name='s', qubits=1, parameter=0.0)
    t = evo.Gate(name='t', qubits=1, parameter=0.0)
    cnot = evo.Gate(name='cx', qubits=2, parameter=0.0)
    gate_set = [hadamard, x, y, z, s, t, cnot]
    
    genome = Genome(gate_set=gate_set, rows = 5, cols = 2)