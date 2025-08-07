from typing import List
from population import Population
from genome import Genome
import random
import numpy as np

class Selection:
    @staticmethod
    def select(population: Population) -> Genome:
        return population.individuals[0]
    
class TournamentSelection(Selection):
    def __init__(self, tournament_size: int = 2):
        self.tournament_size = tournament_size

    def select(self, population: Population) -> Genome:
        selected_individuals = random.sample(population.individuals, self.tournament_size)             
        fittest = min(selected_individuals, key=lambda ind: ind.fitness)
        return fittest
    
class RouletteWheelSelection(Selection):
    def select(self, population: Population) -> Genome:
        pass
    
class StochasticUniversalSampling(Selection):
    def select(self, population: Population, k : int = 1) -> List[Genome]:
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