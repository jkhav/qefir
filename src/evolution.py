from typing import List
from fitness import Fitness
from population import Population
from gate import Gate
from logger import Logger
import copy

class EvolutionManager:
    def __init__(self):
        self.logger = Logger()
    
    def initialize(self, lambda_param, gate_set, max_populations, fitness_function, qubits=2):
        """
        Initialize the evolution manager with parameters for CGP
        """
        self.gate_set = gate_set
        self.lambda_param = lambda_param
        self.gate_set += [Gate(name='SKIP', qubits=0)]
        self.max_populations = max_populations
        self.fitness_function = fitness_function
        self.population = Population(fitness_function=fitness_function) if fitness_function is not None else Population(fitness_function=Fitness())
        self.fittest = None
        self.curr_population = 0
    
    def population_count(self):
        return self.curr_population
    
    def increment_population(self):
        self.curr_population += 1
        
    def cgp_new_population_step(self, fittest):
        """
        Create a new population by mutating the fittest individual
        """
        new_population = Population(self.fitness_function)
        new_population.add_individual(fittest)
        self.logger.log(type='INFO', message=f"Creating new population from fittest individual ")
        self.logger.log(type='DEBUG', message=f"Fittest individual: {fittest}")
        for _ in range(self.lambda_param):
            individual = copy.deepcopy(fittest)
            individual.mutate()
            new_population.add_individual(individual)
        
        new_population.evaluate_fitness()
        for individual in new_population.individuals:
            self.logger.log(type='DEBUG', message=f"Mutated individual: {individual}")
        
        
        self.fittest = new_population.select_fittest()
        self.logger.log(type='INFO', message=f"Population {self.curr_population + 1} evaluated. Fittest fitness: {self.fittest.fitness}")
        self.logger.log(type='DEBUG', message=f"Fittest individual: {self.fittest}")
        
        return new_population
        
    
    def evolve_cgp(self, 
                    lambda_param : int = 4, 
                    gate_set : List[Gate] = [],
                    max_populations : int = 1000, 
                    fitness_function : Fitness = None,
                    max_cols : int = 100, #nc, nr, l - general CGP parameters
                    max_rows : int = 10, # rows == qubits 
                    level_backs : int = 1 # should be redundant
                   ):
        """
        evolve quantum circuit using CGP
        using 1 + lambda strategy
        """
        self.initialize(lambda_param=lambda_param, 
                        gate_set=gate_set, 
                        max_populations=max_populations, 
                        fitness_function=fitness_function,
                        qubits=max_rows)
    
        self.logger.log(type='INFO', message=f"Starting evolution with lambda_param={lambda_param}")
    
        self.population = Population(self.fitness_function).generate_random_population(lambda_param=lambda_param, 
                                                                    gate_set=self.gate_set,
                                                                    max_depth=max_cols,
                                                                    max_qubits=max_rows)
        self.logger.log(type='INFO', message=f"Initial population generated with {len(self.population.individuals)} individuals")
        
        # evaluate the population's fitness
        self.population.evaluate_fitness()
        self.logger.log(type='INFO', message=f"Evaluated initial population fitness")

        # while solution not found or limit not reached
        while self.population.select_fittest().fitness > 0.0 and self.population_count() < self.max_populations:
            # generate new population from the fittest individual
            self.population = self.cgp_new_population_step(self.population.select_fittest())
            self.increment_population()
            
        self.logger.log(type='INFO', message=f"Evolution finished after {self.population_count()} populations")            
        best_individual = self.population.select_fittest()
        self.logger.log(type='INFO', message=f"Best individual found with fitness: {best_individual.fitness}")
        self.logger.log(type='DEBUG', message=f"Best individual: {best_individual}")
        
        self.logger.close()
        return best_individual.to_qiskit_circuit()