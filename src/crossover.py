from genome import Genome
import random
import copy
from logger import Logger
import time

class Crossover:
    """
        Abstract class to implement crossover operations
    """

    @staticmethod
    def crossover(parent1: Genome, parent2: Genome) -> Genome:
        """
            Placeholder for crossover operation implementations
        """
        return parent1
    
class OnePointCrossover(Crossover):
    """
        Class representing one point crossover
    """

    @staticmethod
    def crossover(parent1: Genome, parent2: Genome, logger : Logger) -> Genome:
        """
            Implementation of one point crossover operation
            The crossover point is chosen randomly
            New genome is created by combination of copied genes from the parents
        """
        crossover_point = random.randint(0, len(parent1.genes) - 1)
        
        genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
        child = Genome(gate_set=parent1.gate_set, max_qubits_needed=parent1.max_qubits_needed, qubits=parent1.qubits, operations=parent1.operations)
        copy_start = time.time()
        child.genes = copy.deepcopy(genes)
        copy_end = time.time()
        logger.log_copy(copy_end - copy_start)
        return child

class UniformCrossover(Crossover):
    """
        Class representing uniform crossover
        in this crossover, the crossover is not done by crossover point,
        but each gene is treated separately -- with 50% chance of being taken from one parent or the other
    """

    @staticmethod
    def crossover(parent1: Genome, parent2: Genome, logger : Logger) -> Genome:
        """
            Implementation of uniform crossover operation
            Each gene is treated separately -- with 50% chance of being taken from one parent or the other
        """
        genes = []
        child = Genome(gate_set=parent1.gate_set, max_qubits_needed=parent1.max_qubits_needed, qubits=parent1.qubits, operations=parent1.operations)
        for i in range(len(parent1.genes)):
            if random.random() < 0.5:
                genes.append(parent1.genes[i])
            else:
                genes.append(parent2.genes[i])
        copy_start = time.time()
        child.genes = copy.deepcopy(genes)
        copy_end = time.time()
        logger.log_copy(copy_end - copy_start)
        return child