from typing import List
from fitness import Fitness
from population import Population
from gate import Gate, GateSet
from logger import Logger
import copy
import random
from genome import Genome
from crossover import OnePointCrossover, UniformCrossover
from selection import StochasticUniversalSampling, TournamentSelection
from multithread_fitness import MultiThreadedFitnessEvaluator
import time

class EvolutionManager:
    """
        Class representing the evolution framework
        First, initialize() has to be called to fill in needed information
        needed for the evolution itself

        Specifications to be used in initialize():
            - gate set used in the genomes
            - fitness function (either name from the default functions or a custom callable)
            - max number of populations, max number of operations in a genome
            - mutation rate of active genes and rate of inactive genes
            - crossover rate (if not met, the fittest individual is mutated)
            - allowed error for the fitness function
            - max number of qubits in a genome
            - population size
            - selection method (given name, with needed parameters e.g. Tournament selection - tournament size)
            - crossover method (given name)

        After initialization, call evolve() to start the evolution
        The fittest individual (Genome) is returned
        All information about the evolution is in logs/
    """


    def __init__(self):
        self.logger = Logger()
    
    def initialize(
                    self, 
                    gate_set : GateSet = None,
                    max_populations : int = 1000, 
                    fitness_function : Fitness = None,
                    max_operations : int = 100,
                    active_mut_rate : float = 0.05, # mutation rate of active nodes
                    inactive_mut_rate : float = 0.5, # mutation rate of inactive nodes
                    max_qubits : int = 2,
                    population_size: int = 10,
                    crossover_rate : float = 0.6,
                    allowed_err : float = 0.0,
                    crossover_method : str = 'OnePointCrossover',
                    selection_method : str = 'TournamentSelection',
                    tournament_size : int = 2,
                   ) -> None:
        """
            Initialize the evolution manager with all provided information about the evolution
        """
        self.gate_set = gate_set
        self.gate_set.add_gate(Gate(name='SKIP', qubits=0))
        self.max_populations = max_populations
        self.fitness_function = fitness_function
        self.fitness_evaluator = MultiThreadedFitnessEvaluator(fitness_function=fitness_function, logger=self.logger)
        self.population = Population()
        self.fittest = None
        self.curr_population = 0
        self.active_mut_rate = active_mut_rate
        self.inactive_mut_rate = inactive_mut_rate
        self.max_operations = max_operations
        self.max_qubits = max_qubits
        self.max_qubits_needed = max(self.gate_set.get_gates(), key=lambda g: g.qubits).qubits
        self.population_size = population_size
        if crossover_method == 'OnePointCrossover':
            self.crossover = OnePointCrossover()
        elif crossover_method == 'UniformCrossover':
            self.crossover = UniformCrossover()
        # more crossover methods to be added

        if selection_method == 'TournamentSelection':
            self.selection = TournamentSelection(tournament_size=tournament_size)
        elif selection_method == 'StochasticUniversalSampling':
            self.selection = StochasticUniversalSampling()
        # more selection methods to be added

        self.crossover_rate = crossover_rate
        self.allowed_err = allowed_err

    def population_count(self) -> int:
        """
            Return the current population count
        """
        return self.curr_population
    
    def increment_population(self) -> None:
        """
            Increment the current population count
        """
        self.curr_population += 1
        
    def new_population_step(self) -> Population:
        """
            Proceed to the next generation - create new population,
            add the fittest individual (elitism), create new individuals
            by the selection method, crossover, mutation and add them to the new population
        """
        new_population = Population()
        
        # allow elitism for the fittest individual
        new_population.add_individual(self.fittest)
        new_population.fittest = self.fittest
        for _ in range(self.population_size - 1):
            
            # if the crossover rate is met, do the crossover
            # otherwise, like in CGP, mutate the fittest individual
            prob = random.uniform(0, 1)
            selection_start = time.time()
            parents = self.selection.select(self.population, k=2)
            par1 = parents[0]
            par2 = parents[1]
            selection_end = time.time()
            self.logger.log_selection(selection_end - selection_start)
            if prob < self.crossover_rate:
                crossover_start = time.time()
                child = self.crossover.crossover(par1, par2, logger=self.logger)
                crossover_end = time.time()
                self.logger.log_crossover(crossover_end - crossover_start)

                child.mutate(logger=self.logger, active_mut_rate=self.active_mut_rate, inactive_mut_rate=self.inactive_mut_rate)
                new_population.add_individual(child)
            else:
                # mutate parent with better fitness
                copy_start = time.time()
                if par1.fitness < par2.fitness:
                    child = copy.deepcopy(par1)
                else:
                    child = copy.deepcopy(par2)
                copy_end = time.time()
                self.logger.log_copy(copy_end - copy_start)

                child.mutate(logger=self.logger, active_mut_rate=self.active_mut_rate, inactive_mut_rate=self.inactive_mut_rate)
                new_population.add_individual(child)

        self.fittest = self.fitness_evaluator.evaluate(population=new_population)
        avg_fitness = new_population.average_fitness()
        #print(f"Population {self.curr_population + 1} evaluated. Fittest fitness: {self.fittest.fitness}")
        self.logger.log(type='INFO', message=f"Population {self.curr_population + 1} evaluated. Fittest fitness: {self.fittest.fitness}")
        #self.logger.log(type='DEBUG', message=f"Fittest individual: {self.fittest}")
        
        return new_population



    def evolve(self) -> Genome:
        """
            Evolve a genome representing a quantum circuit based on provided fitness function
        """
        self.logger.log(type='INFO', message=f"Starting evolution")
    
        self.population = Population().generate_random_population( 
                                                                    gate_set=self.gate_set,
                                                                    max_operations=self.max_operations,
                                                                    max_qubits=self.max_qubits,
                                                                    population_size=self.population_size,
                                                                    max_qubits_needed=self.max_qubits_needed
                                                                    )

        self.logger.log(type='INFO', message=f"Initial population generated with {len(self.population.individuals)} individuals")
        
        # evaluate the population's fitness
        self.fittest = self.fitness_evaluator.evaluate(population=self.population)
        self.logger.log(type='INFO', message=f"Evaluated initial population fitness")

        # while solution not found or limit not reached 
        while self.fittest.fitness > (0.0 + self.allowed_err) and self.population_count() < self.max_populations-1:
            self.increment_population()
            self.population = self.new_population_step()

        self.fitness_evaluator.gracefully_terminate_simulator()

        self.logger.log(type='INFO', message=f"Evolution finished after {self.population_count()+1} populations")            
        best_individual = self.fittest
        self.logger.log(type='INFO', message=f"Best individual found with fitness: {best_individual.fitness}")
        self.logger.log(type='DEBUG', message=f"Best individual: {best_individual}")
        self.logger.print_stats()
        self.logger.print_final_circuit(best_individual)
        #self.logger.move_based_on_final_fitness(best_individual.fitness)
        self.logger.close()
        return best_individual