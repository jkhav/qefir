from gene import Gene
from genome import Genome
from fitness import Fitness
import datetime
import time
from logger import Logger
from typing import List
from gate import Gate
from fitness import Fitness

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
        return sorted(self.individuals, key=lambda x: x.fitness)

    def select_fittest(self) -> Genome:
        return self.fittest

    def generate_random_population(
                                    self, 
                                    gate_set : List[Gate], 
                                    max_operations : int, 
                                    max_qubits : int, 
                                    max_qubits_needed : int, 
                                    population_size : int) -> "Population":
        for _ in range(population_size):
            individual = Genome(gate_set=gate_set, qubits=max_qubits, operations=max_operations, max_qubits_needed=max_qubits_needed).generate_random_individual()
            self.add_individual(individual)
        
        return self

    # not needed when using MultiThreadedFitnessEvaluator instead of direct Fitness function
    #def evaluate_fitness(self, logger : Logger = None) -> Genome:
    #    self.fittest = None
    #    for individual in self.individuals:
    #        individual.fitness = self.fitness_function.evaluate(individual, logger)
    #        if self.fittest is None or individual.fitness < self.fittest.fitness:
    #            self.fittest = individual
    #        logger.log(f"Evaluated fitness {individual.fitness} for individual {individual}")
    #    return self.fittest