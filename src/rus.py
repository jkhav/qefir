import sys
import math
import evolution as evo
import numpy as np
import subprocess
import time
from logger import Logger
import quantum_gates as qg

if __name__ == "__main__":
    def sliqsim_fitness(individual, statevectors : list[np.array], logger : Logger):
        def extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, qubits):
            """
            Given statevector is ordered in big endian order, meaning that the amplitudes in a two qubits system
            are in order 00, 10, 01, 11
            This function extracts the amplitudes where all ancilla bits are 0 -- for example states 001, 000 in case non-ancilla idx is 2
            """
            amp0 = 0j
            amp1 = 0j
            for i in range(len(statevector)):
                little_endian_bits = format(i, f'0{qubits}b')
                big_endian_bits = little_endian_bits[::-1]
                if all(big_endian_bits[j] == '0' for j in range(qubits) if j != non_ancilla_idx):
                    if big_endian_bits[non_ancilla_idx] == '0':
                        amp0 += statevector[i]
                    else:
                        amp1 += statevector[i]
            norm = np.sqrt(abs(amp0)**2 + abs(amp1)**2)

            success_probability = abs(amp0)**2 + abs(amp1)**2
            if norm == 0:
                return np.array([1, 0]), 0
            return np.array([amp0, amp1]) / norm, success_probability

        def extract_non_ancilla_qubit_state_fast(statevector, qubits):
            # assume non-ancilla is always qubits-1,
            # that means that we want entries 001, 000 for 3 qubits, 0000 and 0001 for 4 qubits etc.
            amp0 = statevector[0]
            amp1 = statevector[2**(qubits-1)]
            norm = np.sqrt(abs(amp0)**2 + abs(amp1)**2)
            if norm == 0:
                return np.array([0, 0])
            return np.array([amp0, amp1]) / norm  
    
        def fidelity(vec1, vec2):
            inner_product = np.vdot(vec1, vec2)
            return 1.0 - np.pow(np.abs(inner_product), 2)

        def euclidean(vec1, vec2):
            return np.linalg.norm(vec1 - vec2)
    
        def number_of_t_gates(individual):
            count = 0
            for gene in individual.genes:
                if gene.gate == 't' or gene.gate == 'tdg':
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
            
        
        def find_max_depth(individual):
            return 0

        non_ancilla_idx = individual.qubits - 1
        weights = {
            "euclidean": 1,
            "fidelity": 0,
            "t_gate_penalty": 0.00001,
            "low_success_probability_penalty": 0.5,
            "max_depth": 0.000005,
            "gate_count": 0.000005,
        }
        # compute circuit specific metrics
        max_depth = find_max_depth(individual)
        gate_count = gate_count(individual)
        t_gate_penalty = number_of_t_gates(individual)
        

        # (5I + 2jZ) / sqrt(29) -- tmp2.qasm
        #expected_states = [
        #    np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1]),
        #    np.array([1, 0]) * 0 + np.array([0, 1]) * (5 - 2j)/np.sqrt(29),
        #    np.array([1, 0]) * ((5+2j)/np.sqrt(58)) + np.array([0, 1]) * ((5-2j)/np.sqrt(58)), # state +
        #    np.array([1, 0]) * ((5+2j)/np.sqrt(58)) + np.array([0, 1]) * ((-5+2j)/np.sqrt(58)), # state -
        #]

        # (2X + sqrt(2)*Y + Z) / sqrt(7) -- tmp4.qasm
        #expected_states = [
        #    np.array([1, 0]) / np.sqrt(7) + ((np.sqrt(2) * 1j + 2)/np.sqrt(7)) * np.array([0, 1]),
        #    np.array([1, 0]) * ((2 - np.sqrt(2) * 1j)/np.sqrt(7)) + np.array([0, 1]) * (-1)/np.sqrt(7),
        #    np.array([1, 0]) * ((3 - np.sqrt(2) * 1j)/np.sqrt(14)) + np.array([0, 1]) * ((1 + np.sqrt(2) * 1j)/np.sqrt(14)),
        #    np.array([1, 0]) * ((-1 + np.sqrt(2) * 1j)/np.sqrt(14)) + np.array([0, 1]) * ((3 + np.sqrt(2) * 1j)/np.sqrt(14)),
        #]
        
        # (I + sqrt(2)jX)/sqrt(3) -- tmp3.qasm
        #expected_states = [
        #    np.array([1, 0]) / np.sqrt(3) + 1j * np.sqrt(2) * np.array([0, 1]) / np.sqrt(3),
        #    np.array([1, 0]) * ((np.sqrt(2) * 1j)/np.sqrt(3)) + np.array([0, 1]) * (1/np.sqrt(3)),
        #    np.array([1, 0]) * ((1 + np.sqrt(2) * 1j)/np.sqrt(6)) + np.array([0, 1]) * ((1 + np.sqrt(2) * 1j)/np.sqrt(6)),
        #    np.array([1, 0]) * ((1 - np.sqrt(2) * 1j)/np.sqrt(6)) + np.array([0, 1]) * ((-1 + np.sqrt(2) * 1j)/np.sqrt(6)),
        #]
        
        # (I + 2jZ)/sqrt(5) -- tmp5.qasm
        #expected_states = [
        #    np.array([1, 0]) * ((1+2j)/np.sqrt(5)) + np.array([0, 1]) * 0,
        #    np.array([1, 0]) * 0 + np.array([0, 1]) * ((1-2j)/np.sqrt(5)),
        #    np.array([1, 0]) * ((1+2j)/np.sqrt(10)) + np.array([0, 1]) * ((1-2j)/np.sqrt(10)),
        #    np.array([1, 0]) * ((1+2j)/np.sqrt(10)) + np.array([0, 1]) * ((-1+2j)/np.sqrt(10)),
        #]
        
        # (3I + 2jZ)/sqrt(13) -- tmp6.qasm
        expected_states = [
            np.array([1, 0]) * ((3+2j)/np.sqrt(13)) + np.array([0, 1]) * 0,
            np.array([1, 0]) * 0 + np.array([0, 1]) * ((3-2j)/np.sqrt(13)),
            np.array([1, 0]) * ((3+2j)/np.sqrt(26)) + np.array([0, 1]) * ((3-2j)/np.sqrt(26)),
            np.array([1, 0]) * ((3+2j)/np.sqrt(26)) + np.array([0, 1]) * ((-3+2j)/np.sqrt(26)),
        ]        
        
        # (4I + jZ)/sqrt(17) -- tmp7.qasm
        #expected_states = [
        #    np.array([1, 0]) * ((4+1j)/np.sqrt(17)) + np.array([0, 1]) * 0,
        #    np.array([1, 0]) * 0 + np.array([0, 1]) * ((4-1j)/np.sqrt(17)),
        #    np.array([1, 0]) * ((4+1j)/np.sqrt(34)) + np.array([0, 1]) * ((4-1j)/np.sqrt(34)),
        #    np.array([1, 0]) * ((4+1j)/np.sqrt(34)) + np.array([0, 1]) * ((-4+1j)/np.sqrt(34)),
        #]

        fdlt = 0
        euclidean_distance = 0
        success_probability = 0
        success_probability_tmp = 0
        # compute statevector specific metrics
        for i, statevector in enumerate(statevectors):
            statevector, success_probability_tmp = extract_non_ancilla_qubit_state(statevector, non_ancilla_idx, individual.qubits)
            fdlt += fidelity(statevector, expected_states[i])
            euclidean_distance += euclidean(statevector, expected_states[i])
            success_probability += success_probability_tmp
        fdlt /= len(statevectors)
        euclidean_distance /= len(statevectors)
        success_probability /= len(statevectors)
        low_success_probability_penalty = 0 if success_probability > 0.9 else 1 - success_probability
        
        fitness = 0
        fitness += weights["gate_count"] * gate_count
        fitness += weights["euclidean"] * euclidean_distance
        fitness += weights["t_gate_penalty"] * t_gate_penalty
        fitness += weights["low_success_probability_penalty"] * low_success_probability_penalty
        fitness += weights["max_depth"] * max_depth
        fitness += weights["fidelity"] * fdlt
        return fitness

    hadamard = evo.Gate(name='h', qubits=1, parameter=0.0)
    s = evo.Gate(name='s', qubits=1, parameter=0.0)
    t = evo.Gate(name='t', qubits=1, parameter=0.0)
    cnot = evo.Gate(name='cx', qubits=2, parameter=0.0)
    cz = evo.Gate(name='cz', qubits=2, parameter=0.0)
    tdg = evo.Gate(name='tdg', qubits=1, parameter=0.0)
    gate_set = [hadamard, s, t, cnot, cz, tdg]

    def ddsim_fitness(individual, logger : Logger):

        def parse_ddsim_output(res_str):
            """
            Example:
            [0.25-0.25j,0.25+0.25j,0.146447-0.853553j,0+0j,]
            [0.25+0.25j,0.25-0.25j,0+0j,-0.146447+0.853553j,]
            [0.853553-0.146447j,0+0j,-0.25+0.25j,-0.25-0.25j,]
            [0+0j,-0.853553+0.146447j,-0.25-0.25j,-0.25+0.25j,]
            """
            matrix = []
            for line in res_str.split('\n'):
                if line.startswith('['):
                    # Remove brackets and split by comma, then filter out empty strings
                    elements = [x.strip() for x in line.strip('[]').split(',') if x.strip()]
                    # Parse each element as complex number
                    row = []
                    for elem in elements:
                        try:
                            row.append(complex(elem))
                        except ValueError:
                            # Handle cases where the format might be different
                            # Try to parse manually if needed
                            print(f"Warning: Could not parse complex number: {elem}")
                            row.append(0j)
                    matrix.append(row)
            return matrix

        def trace(matrix):
            return sum(matrix[i][i] for i in range(len(matrix)))

        def adjoint(matrix):
            return np.conj(np.transpose(matrix))

        def hadamard_count(individual):
            count = 0
            for gene in individual.genes:
                if gene.gate == 'h':
                    count += 1
            return count

        def reduce_matrix(matrix):
            can_normalize = True
            try:
                q1_matrix = [[matrix[0][0], matrix[0][2]], [matrix[2][0], matrix[2][2]]]
            except IndexError:
                can_normalize = False
                print(f"IndexError: {matrix}")
                return matrix, can_normalize
                for i in range(len(q1_matrix)):
                    norm = np.linalg.norm(q1_matrix[i])
                    if norm == 0:
                        can_normalize = False
                        return q1_matrix, can_normalize
                    q1_matrix[i] = [x / norm for x in q1_matrix[i]]
            return q1_matrix, can_normalize



        qasm_str = individual.to_qasm()
        with open('tmp_circuit.qasm', 'w') as f:
            f.write(qasm_str)

        res = subprocess.run(['./mqt-ddsim-simple', '--simulate_unitary', 'tmp_circuit.qasm', '--pu'], capture_output=True)
        res_str = res.stdout.decode('utf-8')

        if res_str == 'error':
            return 1.0

        matrix = parse_ddsim_output(res_str)
        reduced_matrix, normalized = reduce_matrix(matrix)
        # the result matrix cant be unitary
        if not normalized:
            return 1.0

        # check if the matrix is unitary
        product = reduced_matrix @ adjoint(reduced_matrix)
        if not np.allclose(product, np.eye(len(product))):
            return 1.0

        expected_matrix = (3 * qg.I + 2j * qg.Z) / np.sqrt(13)
        return np.linalg.norm((expected_matrix - reduced_matrix), 'fro')
        # expected_matrix' * reduced_matrix should result in e^jphi * I, the absolute value of trace should be 2^n
        # divide the trace by 2^n to normalize to interval [0, 1]
        trace = np.trace(expected_matrix @ adjoint(reduced_matrix))
        n = 1
        #normalized_trace = np.abs(trace) / (2**n)
        normalized_trace = trace / (2**n)
        print(f"normalized_trace: {normalized_trace}")

        return np.abs(normalized_trace - 1)


    fitness = evo.Fitness(function=ddsim_fitness)
    evolution_manager = evo.EvolutionManager()
    evolution_manager.initialize(
                                gate_set=gate_set,
                                max_populations=250, 
                                max_operations=20,
                                fitness_function=fitness,
                                max_qubits=2,
                                active_mut_rate=0.45,
                                inactive_mut_rate=0.9,
                                crossover_rate=0.45,
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