import sys
import math
import evolution as evo
import numpy as np
import subprocess
import time
from logger import Logger

if __name__ == "__main__":
    def sliqsim_fitness(individual, statevector_0 : np.array, statevector_1 : np.array, logger : Logger):
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
    
        def number_of_t_gates(individual):
            count = 0
            for gene in individual.genes:
                if gene.gate == 't':
                    count += 1
            return count

        def gate_count(individual):
            i = 0
            count = 0
            in_actives = True
            inactives_end = 0
            while i < len(individual.genes):
                gene = individual.genes[i]
                if i > inactives_end:
                    in_actives = True
                    inactives_end = 0
            
                if gene.gate == 'SKIP':
                    in_actives = False
                    inactives_end = i + gene.skips + 1
                
                if in_actives:
                    count += 1
                i += 1
            return count

        def compute_success_probability(statevector):
            return 0
        
        def find_max_depth(individual):
            return 0

        non_ancilla_idx = individual.qubits - 1
        #expected_state_1 = np.array([1, 0]) * 0 + np.array([0, 1]) * (5 - 2j)/np.sqrt(29)
        expected_state_1 = np.array([1, 0]) * ((2 - np.sqrt(2) * 1j)/np.sqrt(7)) + np.array([0, 1]) * (-1)/np.sqrt(7)
        #expected_state_1 = np.array([1, 0]) * ((np.sqrt(2) * 1j)/np.sqrt(3)) + np.array([0, 1]) * (1/np.sqrt(3))
        
        #expected_state_0 = np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1])
        expected_state_0 = np.array([1, 0]) / np.sqrt(7) + ((np.sqrt(2) * 1j + 2)/np.sqrt(7)) * np.array([0, 1])
        #expected_state_0 = np.array([1, 0]) / np.sqrt(3) + 1j * np.sqrt(2) * np.array([0, 1]) / np.sqrt(3)

        weights = {
            "euclidean": 0.9,
            "fidelity": 0.08,
            "t_gate_penalty": 0.00001,
            "success_probability": 0.2,
            "max_depth": 0.000005,
            "gate_count": 0.000005,
        }
        success_probability = (compute_success_probability(statevector_0) + compute_success_probability(statevector_1)) / 2
        max_depth = find_max_depth(individual)

        statevector_0 = extract_non_ancilla_qubit_state(statevector_0, non_ancilla_idx, individual.qubits)
        statevector_1 = extract_non_ancilla_qubit_state(statevector_1, non_ancilla_idx, individual.qubits)
        fidelity = (fidelity(statevector_0, expected_state_0) + fidelity(statevector_1, expected_state_1)) / 2
        euclidean_distance = (euclidean(statevector_0, expected_state_0) + euclidean(statevector_1, expected_state_1)) / 2
        gate_count = gate_count(individual)
        t_gate_penalty = number_of_t_gates(individual)
        
        fitness = 0
        fitness += weights["gate_count"] * gate_count
        fitness += weights["euclidean"] * euclidean_distance
        fitness += weights["t_gate_penalty"] * t_gate_penalty
        fitness += weights["success_probability"] * success_probability
        fitness += weights["max_depth"] * max_depth
        fitness += weights["fidelity"] * fidelity
        return fitness


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
                                max_populations=5000, 
                                max_operations=30,
                                fitness_function=fitness,
                                max_qubits=2,
                                active_mut_rate=0.2,
                                inactive_mut_rate=0.65,
                                crossover_rate=0.6,
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