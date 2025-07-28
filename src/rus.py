import sys
import math
import qiskit
import evolution as evo
import numpy as np
import subprocess
import pennylane as qml
import time
from logger import Logger

if __name__ == "__main__":
    def sliqsim_fitness(individual, logger : Logger):
        def extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, qubits):
            amplitude_0 = 0j
            amplitude_1 = 0j
            for i in range(len(statevector)):
                bits = format(i, f'0{qubits}b')
                if all(bits[-(j+1)] == '0' for j in range(qubits) if j != non_ancilla_idx):
                    if bits[-(non_ancilla_idx+1)] == '0':
                        amplitude_0 = statevector[i]
                    else:
                        amplitude_1 = statevector[i]
            norm = np.sqrt(np.pow(abs(amplitude_0), 2) + np.pow(abs(amplitude_1), 2))
            if norm == 0:
                return np.array([1, 0])
            return np.array([amplitude_0, amplitude_1]) / norm
    
        def fidelity(vec1, vec2):
            inner_product = np.vdot(vec1, vec2)
            return 1.0 - np.pow(np.abs(inner_product), 2)

        def euclidean(vec1, vec2):
            return np.linalg.norm(vec1 - vec2)

        def get_all_basis_states(qubits):
            # for 3 qubits, generate strings '000', '100'
            states = []
            zeroes = '0' * (qubits-1)
            states.append('0' + zeroes)
            states.append('1' + zeroes)
            return states
        
        def parse_sliqsim_output(output : str):
            time_elapsed = 0
            # parse the output {"statevector": [0, 0, 0, 1] }
            statevector = []
            start = output.find('[')
            end = output.find(']')
            vector_str = output[start + 1:end]
            entries = [x.strip() for x in vector_str.split(',')]
            statevector = [complex(e.replace('i', 'j')) for e in entries]
            
            start = output.find('Runtime:')
            start += len('Runtime:')
            end = output.find('seconds', start)
            time_elapsed = float(output[start:end].strip())
            return np.array(statevector), time_elapsed
            
        def number_of_t_gates(individual):
            count = 0
            for gene in individual.genes:
                if gene.gate == 't':
                    count += 1
            return count
        
        # generate qasm file
        time_start = time.time()
        qc = individual.to_qasm()
        time_end = time.time()
        logger.log_conversion(time_end - time_start)
        
        time_start = time.time()
        filename = 'tmp_circuit.qasm'
        with open(filename, 'w') as f:
            f.write(qc)

        non_ancilla_idx = individual.qubits - 1        
        fidelities = []
        basis_states = get_all_basis_states(individual.qubits)
        for state in basis_states:
            expected_state = np.array([1, 0]) * 1 + np.array([0, 1]) * 1
            if state[-(non_ancilla_idx+1)] == '1':
                #expected_state = np.array([1, 0]) * 0 + np.array([0, 1]) * (5 - 2j)/np.sqrt(29)
                expected_state = np.array([1, 0]) * ((2 - np.sqrt(2) * 1j)/np.sqrt(7)) + np.array([0, 1]) * (-1)/np.sqrt(7)
                #expected_state = np.array([1, 0]) * ((np.sqrt(2) * 1j)/np.sqrt(3)) + np.array([0, 1]) * (1/np.sqrt(3))
            else:
                #expected_state = np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1])
                expected_state = np.array([1, 0]) / np.sqrt(7) + ((np.sqrt(2) * 1j + 2)/np.sqrt(7)) * np.array([0, 1])
                #expected_state = np.array([1, 0]) / np.sqrt(3) + 1j * np.sqrt(2) * np.array([0, 1]) / np.sqrt(3)

            res = subprocess.run(['./SliQSim', '--sim_qasm', filename, '--type', '1', '--basis_state', state, '--print_info'], capture_output=True)
            res_str = res.stdout.decode('utf-8')
            print("SliQSim output:")
            print(res_str)
            statevector, time_spent = parse_sliqsim_output(res_str)
            logger.log_sliqsim(time_spent)
            statevector = extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, individual.qubits)
            #dist = fidelity(statevector, expected_state)
            dist = euclidean(statevector, expected_state)
            if dist < 0.0:
                dist = 0.0

            #if np.array_equal(statevector, np.array([1, 0])) or np.array_equal(statevector, np.array([0, 1])):
            #    dist = 1.0
            
            print(f"Distance for state {state}: {dist}")
            fidelities.append(dist)
            
        # calculate the average fidelity
        avg_fidelity = sum(fidelities) / len(fidelities)
        print(f"Average fidelity: {avg_fidelity}")

        t_gate_penalty = number_of_t_gates(individual) * 0.0001

        time_end = time.time()
        logger.log_simulation(time_end - time_start)
        return avg_fidelity + t_gate_penalty


    hadamard = evo.Gate(name='h', qubits=1, parameter=0.0)
    s = evo.Gate(name='s', qubits=1, parameter=0.0)
    t = evo.Gate(name='t', qubits=1, parameter=0.0)
    cnot = evo.Gate(name='cx', qubits=2, parameter=0.0)
    cz = evo.Gate(name='cz', qubits=2, parameter=0.0)
    tdg = evo.Gate(name='tdg', qubits=2, parameter=0.0)
    gate_set = [hadamard, s, t, cnot, cz, tdg]
    
    fitness = evo.Fitness(function=sliqsim_fitness)
    evolution_manager = evo.EvolutionManager()
    evolution_manager.initialize(
                                gate_set=gate_set,
                                max_populations=1000, 
                                max_operations=30,
                                fitness_function=fitness,
                                max_qubits=2,
                                active_mut_rate=0.05,
                                inactive_mut_rate=0.5,
                                crossover_rate=0.6,
                                population_size=10,
                                allowed_err=0.0000000001
                                )
    circuit = evolution_manager.evolve()
    qasm_str = circuit.to_qasm()
    print("Final circuit QASM:")
    print(qasm_str)
    
    # save it into a file
    with open('final_circuit.qasm', 'w') as f:
        f.write(qasm_str)