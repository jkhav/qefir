import sys
import math
import numpy as np
import subprocess
import sys
import matplotlib.pyplot as plt
import time
import os
import re
sys.path.append('../')
import src.quantum_gates as qg
sys.path.append('tests/')

def test(filename):
    def extract_non_ancilla_qubit_state_fast(statevector, qubits):
        # assume non-ancilla is always qubits-1,
        # that means that we want entries 001, 000 for 3 qubits, 0000 and 0001 for 4 qubits etc.
        amp0 = statevector[0]
        amp1 = statevector[2**(qubits-1)]
        norm = np.sqrt(abs(amp0)**2 + abs(amp1)**2)
        if norm == 0:
            return np.array([1, 0])
        return np.array([amp0, amp1]) / norm  

    def parse_statevector(input_str):
        start = input_str.find('[')
        end = input_str.find(']')
        vector_str = input_str[start + 1:end]
        entries = [x.strip() for x in vector_str.split(',')]
        statevector = [complex(e.replace('i', 'j')) for e in entries]
        return statevector



    expected_gate = (2 * qg.X + np.sqrt(2) * qg.Y + qg.Z) / np.sqrt(7)
    #expected_gate = (qg.I + np.sqrt(2) * 1j * qg.X) / np.sqrt(3)
    #expected_gate = (1 * qg.I + 2j * qg.Z) / np.sqrt(5)
    #expected_gate = (3 * qg.I + 2j * qg.Z) / np.sqrt(13)
    #expected_gate = (4 * qg.I + 1j * qg.Z) / np.sqrt(17)
    #expected_gate = (5 * qg.I + 2j * qg.Z) / np.sqrt(29)

    expected_states = [
        expected_gate @ np.array([1, 0]),
        expected_gate @ np.array([0, 1]),
        expected_gate @ np.array([1/np.sqrt(2), 1/np.sqrt(2)]),
        expected_gate @ np.array([1/np.sqrt(2), -1/np.sqrt(2)]),
    ]

    qasm_str = open(filename, 'r').read()
    match = re.search(r'qreg\s+q\[(\d+)\]', qasm_str)
    qubits = int(match.group(1))

    zeros = '0' * (qubits-1)
    # this actually represents states |0> + zeros, |1> + zeros, |+> + zeros, |-> + zeros
    # in state format |q2q1q0>
    basis_states = [zeros + '0', zeros + '1', zeros + '+', zeros + '-']
    for i, basis_state in enumerate(basis_states):
        res = subprocess.run(['../src/SliQSim', '--sim_qasm', filename, '--type', '1', '--basis_state', basis_state], capture_output=True)
        res_str = res.stdout.decode('utf-8')
        statevector = parse_statevector(res_str)

        print(f"- Statevector for |{basis_state[::-1]}>: \n\t{statevector}")
        statevector = extract_non_ancilla_qubit_state_fast(statevector, qubits)
        print(f"\t - Statevector after projection: \n\t\t{statevector}")
        expected_state = expected_states[i].reshape(-1)
        print(f"\t - Expected state: \n\t\t{expected_state}")
        fidelity = 1.0 - (np.abs(np.vdot(statevector, expected_state)) ** 2)
        print(f"\t - Fidelity: \n\t\t{fidelity}")
        print(f"\t - Distance: \n\t\t{np.linalg.norm(statevector - expected_state)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file = sys.argv[1]
        test(file)

    else:
        file = '../src/final_circuit.qasm'
        test(file)