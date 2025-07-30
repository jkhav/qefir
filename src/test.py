import sys
import math
import qiskit
import evolution as evo
import numpy as np
import subprocess
import pennylane as qml
import sys


if __name__ == "__main__":
    def sliqsim_fitness(file = 'final_circuit.qasm'):
        def extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, qubits):
            amp0 = 0j
            amp1 = 0j
            for i in range(len(statevector)):
                bits = format(i, f'0{qubits}b')
                if all(bits[-(j+1)] == '0' for j in range(qubits) if j != non_ancilla_idx):
                    if bits[-(non_ancilla_idx+1)] == '0':
                        amp0 += statevector[i]
                    else:
                        amp1 += statevector[i]
            norm = np.sqrt(abs(amp0)**2 + abs(amp1)**2)
            if norm == 0:
                return np.array([1, 0])
            return np.array([amp0, amp1]) / norm  
               
               
        def fidelity(vec1, vec2):
            return np.abs(1.0 - qml.math.fidelity_statevector(vec1, vec2))
        
        def dist(vec1, vec2):
            return np.linalg.norm(vec1 - vec2)

        def dist2(vec1, vec2):
            return 1.0 - np.pow(np.abs(np.vdot(vec1, vec2)), 2)

        filename = file
        # simulate the circuit with sliqsim
        basis_state = '00'
        res = subprocess.run(['./SliQSim', '--sim_qasm', filename, '--type', '1', '--basis_state', basis_state], capture_output=True)
        res_str = res.stdout.decode('utf-8')
        print("SliQSim output:")
        print(res_str)
        # parse the output {"statevector": [0, 0, 0, 1] }
        statevector = []
        start = res_str.find('[')
        end = res_str.find(']')
        vector_str = res_str[start + 1:end]
        entries = [x.strip() for x in vector_str.split(',')]
        statevector = [complex(e.replace('i', 'j')) for e in entries]
        # project measurement of all ancilla qubits to be 0
        non_ancilla_idx = 2 - 1
        statevector = extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, 2)
        print(f"Statevector after projection: {statevector}")
        # calculate the distance from the expected state
        # approximate (I + i*sqrt(2)*Z) / sqrt(3) for non_ancilla qubit
        #expected_state = np.array([1, 0]) / np.sqrt(3) + 1j * np.sqrt(2) * np.array([0, 1]) / np.sqrt(3)
        #expected_state = np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1])
        expected_state = np.array([1, 0]) * 0 + np.array([0, 1]) * (5 - 2j)/np.sqrt(29)

        # calculate the distance
        dist = dist(statevector, expected_state)
        distance = fidelity(statevector, expected_state)
        dist3 = dist2(statevector, expected_state)
        #dist = np.linalg.norm(statevector - expected_state)
        # normalize the distance to [0, 1]
        if dist > 1.0:
            dist = 1.0
        elif dist < 0.0:
            dist = 0.0
        print(f"Distance: {dist}")
        print(f"Fidelity: {distance}")
        print(f"Inner product: {dist3}")
            
                        
        return dist
    
if len(sys.argv) > 1:
    file = sys.argv[1]
    print(f"Running SliQSim fitness evaluation...")
    print(f"Fitness value: {sliqsim_fitness(file)}")
else:
    print(f"Running SliQSim fitness evaluation...")
    print(f"Fitness value: {sliqsim_fitness()}")