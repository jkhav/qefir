import qiskit
import cirq
import random
import numpy
import datetime

class Fitness:
    
    def __init__(self, function=None):
        self.function = function if function is not None else self.default_fitness_function
        
    def evaluate(self, individual):
        """
        Evaluate the fitness of an individual genome
        using the fitness function specified for the fitness object
        """
        return self.function(individual)
    
    def default_fitness_function(self, individual):
        """
        TODO
        """
        return random.uniform(0, 1)




class Logger:
    def __init__(self, filename='evolution'):
        self.filename = filename + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.log'
        self.file = open(self.filename, 'w')
        self.start_time = datetime.datetime.now()
    
    def log(self, type='MISC', message='default message'):
        """
        Log a message to the log file with runtime since logger creation
        """
        runtime = datetime.datetime.now() - self.start_time
        self.file.write(f"[{type}] (runtime: {runtime}) {message}\n")
    
    def close(self):
        self.file.close()


class Gene:
    def __init__(self, gate='', target=-1, controls=None, parameter=0.0):
        self.gate = gate
        self.target_qubit = target
        self.control_qubits = controls if controls is not None else []
        self.parameter = parameter
        
    def random(self, gate_set=None, max_qubit=2, parameter_range = (-numpy.pi, numpy.pi)):
        self.gate = random.choice(gate_set)
        self.target_qubit = random.randint(0, max_qubit - 1)
        self.control_qubits = random.sample(range(max_qubit), random.randint(0, max_qubit - 1))
        self.parameter = random.uniform(parameter_range[0], parameter_range[1])
    
    def print_gene(self):
        print(f"Gate: {self.gate}, Target: {self.target_qubit}, Controls: {self.control_qubits}, Parameter: {self.parameter}")

    def __str__(self):
        return f"Gene(gate={self.gate}, target_qubit={self.target_qubit}, control_qubits={self.control_qubits}, parameter={self.parameter})"
        


class Genome:
    def __init__(self, mut_prob=0.7, gate_set=None, max_size=10, qubits=2):
        self.genes = []
        self.fitness = 1.0
        self.mutation_prob = mut_prob
        self.gate_set = gate_set if gate_set is not None else ['h', 'cx', 'x', 'y', 'z', 's', 't']
        self.max_size = max_size
        self.qubits = qubits
    
    def generate_random_individual(self): 
        """
        Generate a random individual genome
        initialize self with randomly generated genes satisfying max size
        genes are generated from the gate set specified for the genome
        and the number of qubits specified for the genome
        """
        for _ in range(random.randint(1, self.max_size)):
            gene = Gene()
            gene.random(self.gate_set, self.qubits)
            self.genes.append(gene)
        return self
    
    def print_genome(self):
        """
        Print all genes in the genome and the genome's fitness
        """
        print("Genome:")
        for gene in self.genes:
            gene.print_gene()
        print(f"Fitness: {self.fitness}")
    
    def mutate(self):
        """
        TODO TODO
        """
        return self

    def __str__(self):
        string = f"Genome(fitness={self.fitness}, genes=["
        for gene in self.genes:
            string += str(gene) + ", "
        string += f"]"
        return string
    
    def to_cirq(self):
        pass

class Population:
    
    def __init__(self, fitness_function=Fitness()):
        self.individuals = [] # genomes in the population
        self.fittest = Genome() # the fittest genome
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

    def evaluate_fitness(self):
        """
        Evaluate fitness function for all individuals in the population
        """
        for individual in self.individuals:
            individual.fitness = self.fitness_function.evaluate(individual)
            if individual.fitness <= self.fittest.fitness:
                self.fittest = individual

    def select_fittest(self):
        return self.fittest

    def generate_random_population(self, lambda_param=4, gate_set=None, max_size=10, qubits=2):
        """
        Generate a random population of genomes
        """
        for _ in range(lambda_param + 1):
            individual = Genome(gate_set=gate_set, max_size=max_size, qubits=qubits).generate_random_individual()
            self.add_individual(individual)
        
        return self




class EvolutionManager:
    def __init__(self):
        self.logger = Logger()
    
    def initialize(self, lambda_param, gate_set, max_populations, max_individual_size, fitness_function, qubits=2):
        """
        Initialize the evolution manager with parameters for CGP
        """
        self.lambda_param = lambda_param
        self.gate_set = gate_set
        self.max_populations = max_populations
        self.max_individual_size = max_individual_size
        self.fitness_function = fitness_function
        self.population = Population(fitness_function=fitness_function) if fitness_function is not None else Population(fitness_function=Fitness())
        self.fittest = Genome()
        self.curr_population = 0
        self.max_qubits = qubits
    
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
            individual = fittest.mutate()
            self.logger.log(type='DEBUG', message=f"Mutated individual: {individual}")
            new_population.add_individual(individual)
        
        new_population.evaluate_fitness()
        self.fittest = new_population.select_fittest()
        self.logger.log(type='INFO', message=f"Population {self.curr_population + 1} evaluated. Fittest fitness: {self.fittest.fitness}")
        
        return new_population
        
    
    def evolve_cgp(self, 
                   lambda_param=4, 
                   gate_set=['h', 'cx', 'x', 'y', 'z', 's', 't'],
                   max_populations=1000, 
                   max_qubits=2, 
                   max_individual_size=100,
                   fitness_function=None):
        """
        evolve quantum circuit using CGP
        using 1 + lambda strategy
        """
        self.initialize(lambda_param=lambda_param, 
                        gate_set=gate_set, 
                        max_populations=max_populations, 
                        max_individual_size=max_individual_size,
                        fitness_function=fitness_function,
                        qubits=max_qubits)
    
        self.logger.log(type='INFO', message=f"Starting evolution with lambda_param={lambda_param}")
    
        self.population = Population(self.fitness_function).generate_random_population(lambda_param=lambda_param, 
                                                                  gate_set=gate_set, 
                                                                  max_size=max_individual_size, 
                                                                  qubits=max_qubits)
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
    
    

    def evolve():
        """
        evolve quantum circuit using genetic programming
        """
        pass
    

if __name__ == "__main__":

    circuit = cirq.Circuit(
        cirq.X(cirq.GridQubit(0, 0))**0.5,
        cirq.measure(cirq.GridQubit(0, 0), key='m')
    )
    
    def tmp_fitness_function(individual):
        return random.uniform(0, 1)
    
    fitness = Fitness(function=tmp_fitness_function)
    
    evolution_manager = EvolutionManager()
    evolution_manager.evolve_cgp(lambda_param=4, 
                                 gate_set=['h', 'cx', 'x', 'y', 'z', 's', 't'],
                                 max_populations=10, 
                                 max_individual_size=100, 
                                 fitness_function=fitness, 
                                 max_qubits=len(circuit.all_qubits()))