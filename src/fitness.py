import random
from genome import Genome
from logger import Logger
import numpy as np
import quantum_gates as qg

class Fitness:
    """
    Class representing fitness function that is passed into the evolution algorithm
    The user should specify a fitness function that takes individual as a parameter
    and returns a float value from interval [0, 1] where 1 is the worst fitness

    name options: 'ddsim', 'sliqsim'
    """
    def __init__(self, function = None, name : str = 'default_fitness') -> None:
        if function is None and name == 'default_fitness_function':
            self.function = self.default_fitness_function
            self.name = 'default_fitness'
            return
        
        if function is not None:
            # provided function, use that
            if not callable(function):
                raise ValueError("Fitness function must be callable")
            self.function = function
            self.name = 'custom'
        else:
            if name == 'default_fitness':
                self.function = self.default_fitness_function
            if name == 'ddsim':
                self.function = self.ddsim_fitness
            if name == 'sliqsim':
                # sliqsim_fitness expects statevectors -- usage of multithread_fitness
                self.function = self.sliqsim_fitness
            self.name = name
                
    def evaluate(self, individual : Genome, logger : Logger, statevectors : list[np.array] = None, matrix : np.array = None) -> float:
        """
        Evaluate the fitness of an individual genome
        using the fitness function specified for the fitness object
        """
        if self.name == 'sliqsim':
            return self.function(individual=individual, logger=logger, statevectors=statevectors)
        elif self.name == 'ddsim':
            return self.function(individual=individual, matrix=matrix, logger=logger)
        else:
            return self.function(individual=individual, logger=logger)
    
    def default_fitness_function(self, individual : Genome) -> float:
        """
        Placeholder fitness function if the user did not define one
        """
        return random.uniform(0, 1)

    @staticmethod
    def number_of_t_gates(individual : Genome) -> int:
        count = 0
        for gene in individual.genes:
            if gene.gate == 't' or gene.gate == 'tdg':
                count += 1
        return count

    @staticmethod
    def gate_count(individual : Genome) -> int:
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

    def ddsim_fitness(self, individual : Genome, matrix : np.array, logger : Logger) -> float:
        def adjoint(matrix):
            return np.conj(np.transpose(matrix))

        def hadamard_count(individual):
            count = 0
            for gene in individual.genes:
                if gene.gate == 'h':
                    count += 1
            return count

        def reduce_matrix(matrix, qubits):
            can_normalize = True
            try:
                index = 2**(qubits-1)
                q1_matrix = [[matrix[0][0], matrix[0][index]], [matrix[index][0], matrix[index][index]]]
            except IndexError:
                can_normalize = False
                return matrix, can_normalize
            for i in range(len(q1_matrix)):
                norm = np.linalg.norm(q1_matrix[i])
                if norm == 0:
                    can_normalize = False
                    return q1_matrix, can_normalize
                q1_matrix[i] /= norm
            return q1_matrix, can_normalize


        def print_matrix(matrix):
            # https://stackoverflow.com/questions/17870612/printing-a-two-dimensional-array-in-python
            rows = len(matrix)
            cols = len(matrix[0])
            for i in range(rows):
                print('\t', end = '')
                for j in range(cols):
                    value = matrix[i][j]
                    if np.iscomplexobj(value):
                        print(f"{value.real:8.3f}{value.imag:+.3f}j", end=' ')
                    else:
                        print(f"{float(value):8.3f}", end=' ')
                print()
            print()

        def check_matrix_validity(full_unitary, qubits, logger) -> tuple[bool, float]:
            # extract fail and success matrices, check if they are proportional to identity
            success_matrix = [[full_unitary[0][0], full_unitary[0][2**(qubits-1)]], [full_unitary[2**(qubits-1)][0], full_unitary[2**(qubits-1)][2**(qubits-1)]]]
            fail_matrix = [[full_unitary[1][0], full_unitary[1][2**(qubits-1)]], [full_unitary[2**(qubits)-1][0], full_unitary[2**(qubits)-1][2**(qubits-1)]]]

            res = success_matrix @ adjoint(success_matrix)
            norm1 = res[0][0]
            if norm1 == 0:
                return False, 0
            if not np.allclose(res, np.eye(len(res))):
                return False, 0

            res = fail_matrix @ adjoint(fail_matrix)
            norm2 = res[0][0]
            if norm2 == 0:
                return True, 1 # this matrix is valid because it has constant probability of success
            res /= norm2
            if not np.allclose(res, np.eye(len(res))):
                return False, 0

            """
            print()
            print(f"|N> Success_p: {norm1} + Fail_p: {norm2} = {norm1 + norm2}")
            
            state = np.array([1, 0, 0, 0])
            res = full_unitary @ state
            norm1 = np.abs(res[0])**2 + np.abs(res[2])**2
            norm2 = np.abs(res[1])**2 + np.abs(res[3])**2
            print(f"|0> Success_p: {norm1} + Fail_p: {norm2} = {norm1 + norm2}")

            state = np.array([0, 0, 1, 0])
            res = full_unitary @ state
            norm1 = np.abs(res[0])**2 + np.abs(res[2])**2
            norm2 = np.abs(res[1])**2 + np.abs(res[3])**2
            print(f"|1> Success_p: {norm1} + Fail_p: {norm2} = {norm1 + norm2}")

            state = np.array([np.sqrt(2)/2, 0, np.sqrt(2)/2, 0])
            res = full_unitary @ state
            norm1 = np.abs(res[0])**2 + np.abs(res[2])**2
            norm2 = np.abs(res[1])**2 + np.abs(res[3])**2
            print(f"|+> Success_p: {norm1} + Fail_p: {norm2} = {norm1 + norm2}")
            print()
            """
            return True, norm1

        valid, success_prob = check_matrix_validity(matrix, individual.qubits, logger)
        if not valid:
            return 500.0

        reduced_matrix, normalized = reduce_matrix(matrix, individual.qubits)
        # the result matrix cant be unitary
        if not normalized:
            return 100.0

        # check if the matrix is unitary
        product = reduced_matrix @ adjoint(reduced_matrix)
        if not np.allclose(product, np.eye(len(product))):
            return 50.0

        #expected_gate = (2 * qg.X + np.sqrt(2) * qg.Y + qg.Z) / np.sqrt(7)
        #expected_gate = (qg.I + np.sqrt(2) * 1j * qg.X) / np.sqrt(3)
        #expected_gate = (1 * qg.I + 2j * qg.Z) / np.sqrt(5)
        expected_gate = (3 * qg.I + 2j * qg.Z) / np.sqrt(13)
        #expected_gate = (4 * qg.I + 1j * qg.Z) / np.sqrt(17)
        #expected_gate = (5 * qg.I + 2j * qg.Z) / np.sqrt(29)

        # only 1 non-ancilla qubit -> single qubit unitary
        matrix_dimension = 2**(1)
        # https://quantumcomputing.stackexchange.com/questions/27690/what-is-fidelity-in-quantum-computing/27696#27696
        fidelity = np.abs(1 - ((1/matrix_dimension**2) * np.abs(np.trace(expected_gate @ adjoint(reduced_matrix)))**2))
        number_of_gates = self.gate_count(individual)
        number_of_t_gates = self.number_of_t_gates(individual)
        prob_penalty = 1 - success_prob
        fitness = 0
        fitness += 0.00000001 * number_of_gates
        fitness += 0.000001 * number_of_t_gates
        fitness += 0.01 * prob_penalty
        fitness += fidelity
        return fitness

    def sliqsim_fitness(self, individual : Genome, statevectors : list[np.array], logger : Logger):
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
        gate_count = self.gate_count(individual)
        t_gate_penalty = self.number_of_t_gates(individual)
        

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

    def get_name(self) -> str:
        return self.name