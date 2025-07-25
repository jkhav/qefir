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

        def euclidean(vec1, vec2):
            return np.linalg.norm(vec1 - vec2) / np.sqrt(2)

        def get_all_basis_states(qubits):
            # for 2 qubits, generate strings '00', '01', '10', '11'
            states = []
            for i in range(2**qubits):
                states.append(format(i, f'0{qubits}b'))
            return states
        
        def parse_sliqsim_output(output : str):
            # parse the output {"statevector": [0, 0, 0, 1] }
            statevector = []
            start = res_str.find('[')
            end = res_str.find(']')
            vector_str = res_str[start + 1:end]
            entries = [x.strip() for x in vector_str.split(',')]
            statevector = [complex(e.replace('i', 'j')) for e in entries]
            return np.array(statevector)
            
        # generate qasm file
        qc = individual.to_qasm()
        filename = 'tmp_circuit.qasm'
        with open(filename, 'w') as f:
            f.write(qc)
        
        # project measurement of all ancilla qubits to be 0
        # calculate the distance from the expected state
        # approximate (I + i*sqrt(2)*X) / sqrt(3) for non_ancilla qubit
        #expected_state = np.array([1, 0]) / np.sqrt(3) + 1j * np.sqrt(2) * np.array([0, 1]) / np.sqrt(3)
        # (2X + sqrt(2)*Y + Z) / sqrt(7)
        #expected_state = np.array([1, 0]) / np.sqrt(7) + ((np.sqrt(2) * 1j + 2)/np.sqrt(7)) * np.array([0, 1])
        # (5I + 2iZ)/sqrt(29)
        #expected_state = np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1])
        
        non_ancilla_idx = individual.qubits - 1        
        fidelities = []
        basis_states = get_all_basis_states(individual.qubits)
        for state in basis_states:
            expected_state = np.array([1, 0]) * 1 + np.array([0, 1]) * 1
            if state[non_ancilla_idx] == '1':
                expected_state = np.array([1, 0]) * 0 + np.array([0, 1]) * (5 + 2j)/np.sqrt(29)
                #expected_state = np.array([1, 0]) * ((2 - np.sqrt(2) * 1j)/np.sqrt(7)) + np.array([0, 1]) * (-1)/np.sqrt(7)
            else:
                expected_state = np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1])
                #expected_state = np.array([1, 0]) / np.sqrt(7) + ((np.sqrt(2) * 1j + 2)/np.sqrt(7)) * np.array([0, 1])

            res = subprocess.run(['./SliQSim', '--sim_qasm', filename, '--type', '1', '--basis_state', state], capture_output=True)
            res_str = res.stdout.decode('utf-8')
            print("SliQSim output:")
            print(res_str)
            statevector = parse_sliqsim_output(res_str)
            statevector = extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, individual.qubits)
            #dist = fidelity(statevector, expected_state)
            dist = euclidean(statevector, expected_state)
            if dist > 1.0:
                dist = 1.0
            elif dist < 0.0:
                dist = 0.0
            print(f"Distance: {dist}")
            fidelities.append(dist)
            
        # calculate the average fidelity
        avg_fidelity = sum(fidelities) / len(fidelities)
        print(f"Average fidelity: {avg_fidelity}")

        return avg_fidelity


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