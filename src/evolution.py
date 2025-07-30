from typing import List
from fitness import Fitness
from population import Population
from gate import Gate
from logger import Logger
import copy
import selection
import crossover
import random
from genome import Genome
from selection import StochasticUniversalSampling
from multithread_fitness import MultiThreadedFitnessEvaluator
import time

class EvolutionManager:
    def __init__(self):
        self.logger = Logger()
    
    def initialize(
                    self, 
                    gate_set : List[Gate] = [],
                    max_populations : int = 1000, 
                    fitness_function : Fitness = None,
                    max_operations : int = 100,
                    active_mut_rate : float = 0.05, # mutation rate of active nodes
                    inactive_mut_rate : float = 0.5, # mutation rate of inactive nodes
                    max_qubits : int = 2,
                    population_size: int = 10,
                    crossover_rate : float = 0.6,
                    allowed_err : float = 0.0
                   ) -> None:
        self.gate_set = gate_set
        self.gate_set += [Gate(name='SKIP', qubits=0)]
        self.max_populations = max_populations
        self.fitness_function = fitness_function
        self.fitness_evaluator = MultiThreadedFitnessEvaluator(fitness_function=fitness_function)
        self.population = Population(self.fitness_evaluator)
        self.fittest = None
        self.curr_population = 0
        self.active_mut_rate = active_mut_rate
        self.inactive_mut_rate = inactive_mut_rate
        self.max_operations = max_operations
        self.max_qubits = max_qubits
        self.max_qubits_needed = max(gate_set, key=lambda g: g.qubits).qubits
        self.population_size = population_size
        self.selection = selection.TournamentSelection(tournament_size=2)
        self.crossover = crossover.OnePointCrossover()
        self.crossover_rate = crossover_rate
        self.allowed_err = allowed_err

    def population_count(self) -> int:
        return self.curr_population
    
    def increment_population(self) -> None:
        self.curr_population += 1
        
    def new_population_step(self) -> Population:
        new_population = Population(self.fitness_evaluator)
        
        # allow elitism for the fittest individual
        new_population.add_individual(self.fittest)
        new_population.fittest = self.fittest
        for _ in range(self.population_size - 1):
            
            # if the crossover rate is met, do the crossover
            # otherwise, like in CGP, mutate the fittest individual
            prob = random.uniform(0, 1)
            selection = StochasticUniversalSampling()
            if prob < self.crossover_rate:
                selection_start = time.time()
                parents = selection.select(self.population, k=2)
                selection_end = time.time()
                self.logger.log_selection(selection_end - selection_start)
                par1 = parents[0]
                par2 = parents[1]
                #par1 = self.selection.select(self.population)
                #par2 = self.selection.select(self.population)

                crossover_start = time.time()
                child = self.crossover.crossover(par1, par2)
                crossover_end = time.time()
                self.logger.log_crossover(crossover_end - crossover_start)
                self.logger.log(type='DEBUG', message=f"Selected parent1 {par1}")
                self.logger.log(type='DEBUG', message=f"Selected parent2 {par2}")
                self.logger.log(type='DEBUG', message=f"Created child before mutation {child}")
                child.mutate(logger=self.logger, active_mut_rate=self.active_mut_rate, inactive_mut_rate=self.inactive_mut_rate)
                new_population.add_individual(child)
            else:
                child = self.fittest.copy()
                child.mutate(logger=self.logger, active_mut_rate=self.active_mut_rate, inactive_mut_rate=self.inactive_mut_rate)
                new_population.add_individual(child)
            self.logger.log(type='DEBUG', message=f"Created child {child}").
        self.fittest = self.fitness_evaluator.evaluate(population=new_population, logger=self.logger)
        self.logger.log(type='INFO', message=f"Population {self.curr_population + 1} evaluated. Fittest fitness: {self.fittest.fitness}")
        self.logger.log(type='DEBUG', message=f"Fittest individual: {self.fittest}")
        
        return new_population



    def evolve(self) -> Genome:
        self.logger.log(type='INFO', message=f"Starting evolution")
    
        self.population = Population(self.fitness_evaluator).generate_random_population( 
                                                                    gate_set=self.gate_set,
                                                                    max_operations=self.max_operations,
                                                                    max_qubits=self.max_qubits,
                                                                    population_size=self.population_size,
                                                                    max_qubits_needed=self.max_qubits_needed
                                                                    )

        self.logger.log(type='INFO', message=f"Initial population generated with {len(self.population.individuals)} individuals")
        
        # evaluate the population's fitness
        self.fittest = self.fitness_evaluator.evaluate(self.population, logger=self.logger)
        self.logger.log(type='INFO', message=f"Evaluated initial population fitness")

        # while solution not found or limit not reached
        while self.fittest.fitness > (0.0 + self.allowed_err) and self.population_count() < self.max_populations-1:
            self.increment_population()
            self.population = self.new_population_step()


        self.logger.log(type='INFO', message=f"Evolution finished after {self.population_count()+1} populations")            
        best_individual = self.fittest
        self.logger.log(type='INFO', message=f"Best individual found with fitness: {best_individual.fitness}")
        self.logger.log(type='DEBUG', message=f"Best individual: {best_individual}")
        self.logger.print_stats()
        self.logger.print_final_circuit(best_individual)
        self.logger.close()
        return best_individual