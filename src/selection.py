from typing import List
from population import Population
from genome import Genome
import random
import numpy as np

class Selection:
    """
        Abstract class to implement selection operators
    """

    @staticmethod
    def select(population: Population, k : int = 1) -> List[Genome]:
        """
            Placeholder for selection operator implementations
            each select() also has k parameters indicating how many genomes to select for unification of all methods
        """
        selected_individuals = random.sample(population.individuals, k)
        return selected_individuals
    
class TournamentSelection(Selection):
    """
        Class representing tournament selection
    """

    def __init__(self, tournament_size: int = 2):
        self.tournament_size = tournament_size

    def select_one(self, population: Population) -> Genome:
        """
            Select one genome from the population based on the tournament selection method
            Randomly choose tournament_size genomes, return the fittest one
        """
        selected_individuals = random.sample(population.individuals, self.tournament_size)             
        fittest = min(selected_individuals, key=lambda ind: ind.fitness)
        return fittest

    def select(self, population: Population, k : int = 1) -> List[Genome]:
        """
            Select k genomes based on k tournaments
        """
        selected_individuals = []
        for _ in range(k):
            selected_individuals.append(self.select_one(population))
        return selected_individuals
    
    
class StochasticUniversalSampling(Selection):
    """
        Class representing stochastic universal sampling method
        https://en.wikipedia.org/wiki/Stochastic_universal_sampling
    """

    def select(self, population: Population, k : int = 1) -> List[Genome]:
        """
            Select k genomes based on stochastic universal sampling multiple pointer method
        """
        ordered_population = population.sort_by_fitness()
        sum = 0
        for individual in ordered_population:
            sum += individual.fitness
        start = random.uniform(0, sum / len(ordered_population))
        pointers = [start + i * (sum / len(ordered_population)) for i in range(k)]
        selected_individuals = []
        for pointer in pointers:
            i = 0        
            fitness_sum = 0
            while fitness_sum < pointer:
                i += 1
                fitness_sum += ordered_population[i].fitness
            selected_individuals.append(ordered_population[i])
        return selected_individuals