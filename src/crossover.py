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
        crossover_start = time.time()
        child.genes = copy.deepcopy(genes)
        crossover_end = time.time()
        logger.log_copy(crossover_end - crossover_start)
        return child