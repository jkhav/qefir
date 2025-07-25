from gene import Gene
from genome import Genome
from fitness import Fitness
import datetime
import time
from logger import Logger
from typing import List
from gate import Gate

class Population:
    def __init__(self, fitness_function=Fitness()) -> None:
        self.individuals = [] # genomes in the population
        self.fittest = None
        self.fitness_function = fitness_function

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

    def evaluate_fitness(self, logger : Logger) -> None:
        """
        Evaluate fitness function for all individuals in the population
        """
        for individual in self.individuals:
            time_start = time.time()
            
            # mutation did not change anything 
            # or skip evaluation of whats already evaluated
            if not individual.first_evaluation and (individual.actives_mutated == 0 or individual == self.fittest):
                if individual != self.fittest:
                    logger.log(type="DEBUG", message=f"Skipped fitness evaluation for individual {individual}")
                continue
            individual.first_evaluation = False
            individual.fitness = self.fitness_function.evaluate(individual)
            logger.log(type="DEBUG", message=f"Evaluated fitness for individual {individual} with fitness {individual.fitness}")
            time_end = time.time()
            logger.log_fitness_call(time_end - time_start)
            
            if self.fittest == None:
                self.fittest = individual
            
            if individual.fitness <= self.fittest.fitness:
                self.fittest = individual
                
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
            print(f"Generated individual: {individual}")
            self.add_individual(individual)
        
        return self


