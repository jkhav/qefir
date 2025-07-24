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