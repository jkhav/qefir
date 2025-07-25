from genome import Genome
import random

class Crossover:
    @staticmethod
    def crossover(parent1: Genome, parent2: Genome) -> Genome:
        return parent1
    
class OnePointCrossover(Crossover):
    
    @staticmethod
    def crossover(parent1: Genome, parent2: Genome) -> Genome:
        crossover_point = random.randint(0, len(parent1.genes) - 1)
        
        # Create a new genome by combining genes from both parents
        new_genes = parent1.genes[:crossover_point] + parent2.genes[crossover_point:]
        child = Genome(gate_set=parent1.gate_set, max_qubits_needed=parent1.max_qubits_needed, qubits=parent1.qubits, operations=parent1.operations)
        child.genes = new_genes
        return child