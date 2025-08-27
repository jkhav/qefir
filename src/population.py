from genome import Genome
from typing import List
from gate import Gate

class Population:
    def __init__(self) -> None:
        self.individuals = [] # genomes in the population
        self.fittest = None

    def add_individual(self, individual: Genome) -> None:
        """
            Add an individual genome to the population
        """
        self.individuals.append(individual)

    def print_population(self) -> None:
        """
            Print all individuals in the population
        """
        print("Population:")
        for individual in self.individuals:
            individual.print_genome()

    def sort_by_fitness(self) -> List[Genome]:
        """
            Sort the inviduals in the population by their fitness value in ascending order
        """
        return sorted(self.individuals, key=lambda x: x.fitness)

    def select_fittest(self) -> Genome:
        """
            Get the fittest individual in the population
        """
        return self.fittest

    def generate_random_population(
                                    self, 
                                    gate_set : List[Gate], 
                                    max_operations : int, 
                                    max_qubits : int, 
                                    max_qubits_needed : int, 
                                    population_size : int) -> "Population":
        """
            Initial step in the GA -- generate a population of completely random genomes
        """
        for _ in range(population_size):
            individual = Genome(gate_set=gate_set, qubits=max_qubits, operations=max_operations, max_qubits_needed=max_qubits_needed).generate_random_individual()
            self.add_individual(individual)
        
        return self

    def average_fitness(self) -> float:
        """
            Get the average fitness value of the population
            consider only non-error values of fitness function
            (some genomes may have fitness value e.g. 500 indicating a genome that cannot be interpreted)
        """
        return sum(individual.fitness for individual in self.individuals if individual.fitness <= 5) / len(self.individuals)