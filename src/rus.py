import sys
import math
import qiskit
import evolution as evo
import numpy as np
import subprocess
import pennylane as qml

if __name__ == "__main__":
    def sliqsim_fitness(individual):
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
                return np.array([0, 0])
            return np.array([amp0, amp1]) / norm
    
        def fidelity(vec1, vec2):
            inner_product = np.vdot(vec1, vec2)
            return 1.0 - np.pow(np.abs(inner_product), 2)

        
        # generate qasm file
        qc = individual.to_qasm()
        filename = 'tmp_circuit.qasm'
        with open(filename, 'w') as f:
            f.write(qc)
        # simulate the circuit with sliqsim
        basis_state = '0' * individual.qubits 
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
        non_ancilla_idx = individual.qubits - 1
        statevector = extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, individual.qubits)
        
        
        
        # calculate the distance from the expected state
        # approximate (I + i*sqrt(2)*X) / sqrt(3) for non_ancilla qubit
        expected_state = np.array([1, 0]) / np.sqrt(3) + 1j * np.sqrt(2) * np.array([0, 1]) / np.sqrt(3)
        
        # (2X + sqrt(2)*Y + Z) / sqrt(7)
        #expected_state = np.array([1, 0]) / np.sqrt(7) + ((np.sqrt(2) * 1j + 2)/np.sqrt(7)) * np.array([0, 1])
        
        # (5I + 2iZ)/sqrt(29)
        #expected_state = np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1])
        
        
        # calculate the distance
        dist = fidelity(statevector, expected_state)
        # normalize the distance to [0, 1]
        if dist > 1.0:
            dist = 1.0
        elif dist < 0.0:
            dist = 0.0
        print(f"Distance: {dist}")
            
                        
        return dist
    
    
    hadamard = evo.Gate(name='h', qubits=1, parameter=0.0)
    s = evo.Gate(name='s', qubits=1, parameter=0.0)
    t = evo.Gate(name='t', qubits=1, parameter=0.0)
    cnot = evo.Gate(name='cx', qubits=2, parameter=0.0)
    cz = evo.Gate(name='cz', qubits=2, parameter=0.0)
    gate_set = [hadamard, s, t, cnot]
    
    fitness = evo.Fitness(function=sliqsim_fitness)
    evolution_manager = evo.EvolutionManager()
    evolution_manager.initialize(
                                gate_set=gate_set,
                                max_populations=5000, 
                                max_operations=15,
                                fitness_function=fitness,
                                max_qubits=2,
                                active_mut_rate=0.05,
                                inactive_mut_rate=0.5,
                                crossover_rate=0.8,
                                population_size=100,
                                allowed_err=0.0000000001
                                )
    circuit = evolution_manager.evolve()
    qasm_str = circuit.to_qasm()
    print("Final circuit QASM:")
    print(qasm_str)
    
    # save it into a file
    with open('final_circuit.qasm', 'w') as f:
        f.write(qasm_str)