from genome import Genome
import random
import copy

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
    def crossover(parent1: Genome, parent2: Genome) -> Genome:
        """
            Implementation of one point crossover operation
            The crossover point is chosen randomly
            New genome is created by combination of copied genes from the parents
        """
        crossover_point = random.randint(0, len(parent1.genes) - 1)
        
        parent1_genes = copy.deepcopy(parent1.genes[:crossover_point])
        parent2_genes = copy.deepcopy(parent2.genes[crossover_point:])
        new_genes = parent1_genes + parent2_genes
        child = Genome(gate_set=parent1.gate_set, max_qubits_needed=parent1.max_qubits_needed, qubits=parent1.qubits, operations=parent1.operations)
        child.genes = new_genes
        return child
