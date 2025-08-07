import random
from genome import Genome
from logger import Logger
import numpy as np

class Fitness:
    """
    Class representing fitness function that is passed into the evolution algorithm
    The user should specify a fitness function that takes individual as a parameter
    and returns a float value from interval [0, 1] where 1 is the worst fitness    
    """
    def __init__(self, function = None, name : str = 'default_fitness_function') -> None:
        if function is None and name == 'default_fitness_function':
            self.function = self.default_fitness_function
            return
        
        if function is not None:
            # provided function, use that
            if not callable(function):
                raise ValueError("Fitness function must be callable")
            self.function = function
        else:
            if name == 'default_fitness_function':
                self.function = self.default_fitness_function
                
    def evaluate(self, individual : Genome, logger : Logger = None) -> float:
        """
        Evaluate the fitness of an individual genome
        using the fitness function specified for the fitness object
        """
        return self.function(individual, logger)
    
    def default_fitness_function(self, individual : Genome) -> float:
        """
        Placeholder fitness function if the user did not define one
        """
        return random.uniform(0, 1)