from gene import Gene
from genome import Genome
from fitness import Fitness
import datetime
import time

class Population:
    def __init__(self, fitness_function=Fitness()):
        self.individuals = [] # genomes in the population
        self.fittest = None
        self.fitness_function = fitness_function
        
    def add_individual(self, individual):
        """
        Add an individual genome to the population
        """
        self.individuals.append(individual)
    
    def print_population(self):
        """
        Print all individuals in the population
        """
        print("Population:")
        for individual in self.individuals:
            individual.print_genome()

    def evaluate_fitness(self, logger=None):
        """
        Evaluate fitness function for all individuals in the population
        """
        for individual in self.individuals:
            time_start = time.time()
            
            # mutation did not change anything 
            # or skip evaluation of whats already evaluated
            if individual.actives_mutated == 0 or individual == self.fittest:
                if individual != self.fittest:
                    logger.log(type="DEBUG", message=f"Skipped fitness evaluation for individual {individual}")
                continue
            
            individual.fitness = self.fitness_function.evaluate(individual)
            time_end = time.time()
            if logger is not None:
                logger.log_fitness_call(time_end - time_start)
            
            if self.fittest == None:
                self.fittest = individual
            
            if individual.fitness <= self.fittest.fitness:
                self.fittest = individual

    def select_fittest(self):
        return self.fittest

    def generate_random_population(self, lambda_param=4, gate_set=None, gates=None, max_depth=100, max_qubits=10):
        """
        Generate a random population of genomes
        """
        for _ in range(lambda_param + 1):
            individual = Genome(gate_set=gate_set, rows=max_qubits, cols=max_depth).generate_random_individual()
            print(f"Generated individual: {individual}")
            self.add_individual(individual)
        
        return self


