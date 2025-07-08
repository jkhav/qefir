from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit_sliqsim_provider import SliQSimProvider
import random
import numpy
import datetime
import math

class Fitness:
    """
        Class representing fitness function that is passed into the evolution algorithm
        The user should specify a fitness function that takes individual as a parameter
        and returns a float value from interval [0, 1] where 1 is the worst fitness
        
    """
    def __init__(self, function=None):
        self.function = function if function is not None else self.default_fitness_function
        
    def evaluate(self, individual):
        """
        Evaluate the fitness of an individual genome
        using the fitness function specified for the fitness object
        """
        return self.function(individual)
    
    def default_fitness_function(self, individual):
        return random.uniform(0, 1)




class Logger:
    def __init__(self, filename='logs/evolution'):
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
        
    def random(self, gate_set=None, max_qubit=2, parameter_range = (-numpy.pi, numpy.pi), max_skips=0):
        self.gate = random.choice(gate_set)
        self.target_qubit = random.randint(0, max_qubit - 1)
        self.control_qubits = random.sample(range(max_qubit), random.randint(0, max_qubit - 1))
        self.parameter = random.uniform(parameter_range[0], parameter_range[1])
        self.skips = random.randint(0, max_skips)

    def print_gene(self):
        print(f"Gate: {self.gate}, Target: {self.target_qubit}")

    def __str__(self):
        return f"{self.gate}[{self.target_qubit}]"
        


class Genome:
    def __init__(self, mut_prob=0.7, gate_set=None, max_qubits=10, max_depth=100):
        self.genes = []
        self.fitness = math.inf
        self.mutation_prob = mut_prob # in CGP, mutation is 1.0
        self.gate_set = gate_set if gate_set is not None else ['h', 'x', 'y', 'z', 's', 't']
        self.gate_set += ['SKIP']
        self.max_depth = max_depth
        self.max_qubits = max_qubits
        self.curr_cols = 0
        self.curr_rows = 0
    
    def generate_random_individual(self): 
        """
        Generate a random individual genome
        initialize self with randomly generated genes satisfying max size
        genes are generated from the gate set specified for the genome
        and the number of qubits specified for the genome
        """
        self.curr_rows = self.max_qubits
        self.curr_cols = self.max_depth
        num_of_genes = self.curr_rows * self.curr_cols
        qubit = 0
        for i in range(num_of_genes):
            curr_col = i // self.curr_rows
            max_skips = self.max_depth - curr_col - 1
            if max_skips < 0:
                max_skips = 0
            gene = Gene()
            gene.random(gate_set=self.gate_set, max_qubit=self.max_qubits, max_skips=max_skips)
            gene.target_qubit = qubit
            self.genes.append(gene)
            qubit += 1
            if qubit >= self.max_qubits:
                qubit = 0
        self.fitness = 1.0
        return self
    
    def print_genome(self):
        """
        Print all genes in the genome and the genome's fitness
        """
        print("Genome:")
        for gene in self.genes:
            print(f"Gene: {gene.gate}, Target: {gene.target_qubit}")
        print(f"Fitness: {self.fitness}")
    
    def mutate(self):
        prob_change_gate = 1
        # TODO add more mutations
        
        assert prob_change_gate == 1.0, "Mutation probabilities must sum to 1"
        
        random_val = random.uniform(0, 1)
        new_individual = self
        
        return new_individual.mutate_change_gate()

    def mutate_change_gate(self):
        gene = random.choice(self.genes)
        gene.gate = random.choice(self.gate_set)
        return self

    def __str__(self):
        string = f"Genome(fitness={self.fitness}, genes=["
        for gate in self.genes:
            string += str(gate) + ", "
        string += f"]"
        return string
    
    def to_qasm(self):
        """
        Convert the genome's phenotype to QASM string format
        for quantum circuit simulation
        SKIP 'gate' is used to skip a certain amount of columns in the circuit
        for higher variability of the circuit
        """
        qasm_string = "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[{}];\n".format(self.max_qubits)
        i = 0
        while i < len(self.genes):
            if self.genes[i].gate == 'SKIP':
                # skip next N gates in self.genes
                i += self.genes[i].target_qubit + 1
                continue
            else:
                gene = self.genes[i]
                qasm_string += "{} q[{}];\n".format(gene.gate, gene.target_qubit)
            i += 1
            
        return qasm_string

    def to_qiskit_circuit(self):
        """
        Convert the genome's phenotype to Qiskit QuantumCircuit object
        for quantum circuit simulation
        SKIP 'gate' is used to skip a certain amount of columns in the circuit
        for higher variability of the circuit
        """
        qr = QuantumRegister(self.max_qubits)
        cr = ClassicalRegister(self.max_qubits)
        qc = QuantumCircuit(qr, cr)
        i = 0
        while i < len(self.genes):
            if self.genes[i].gate == 'SKIP':
                # skip next N gates in self.genes
                i += self.genes[i].target_qubit + 1
                continue
            else:
                gene = self.genes[i]
                if gene.gate == 'h':
                    qc.h(gene.target_qubit)
                elif gene.gate == 'x':
                    qc.x(gene.target_qubit)
                elif gene.gate == 'y':
                    qc.y(gene.target_qubit)
                elif gene.gate == 'z':
                    qc.z(gene.target_qubit)
                elif gene.gate == 's':
                    qc.s(gene.target_qubit)
                elif gene.gate == 't':
                    qc.t(gene.target_qubit)
            i += 1
        # Add measurement to all qubits
        qc.measure(qr, cr)
        return qc
                

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

    def generate_random_population(self, lambda_param=4, gate_set=None, max_depth=100, max_qubits=10):
        """
        Generate a random population of genomes
        """
        for _ in range(lambda_param + 1):
            individual = Genome(gate_set=gate_set, max_qubits=max_qubits, max_depth=max_depth).generate_random_individual()
            self.add_individual(individual)
        
        return self




class EvolutionManager:
    def __init__(self):
        self.logger = Logger()
    
    def initialize(self, lambda_param, gate_set, max_populations, fitness_function, qubits=2):
        """
        Initialize the evolution manager with parameters for CGP
        """
        self.lambda_param = lambda_param
        self.gate_set = gate_set
        self.gate_set += ['SKIP']
        self.max_populations = max_populations
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
                    gate_set=[],
                    max_populations=1000, 
                    fitness_function=None,
                    max_cols=1000, #nc, nr, l - general CGP parameters
                    max_rows=10, # rows == qubits 
                    level_backs=1 # should be redundant
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
                                                                    gate_set=gate_set, 
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

if __name__ == "__main__":
    def tmp_fitness_function(individual):   
        def l2_distance(p, q):
            keys = set(p) | set(q)
            return math.sqrt(sum((p.get(k, 0) - q.get(k, 0))**2 for k in keys))
        
        def normalize(dist):
            total = sum(dist.values())
            return {k: v / total for k, v in dist.items()}
                 
        qr = QuantumRegister(5)
        cr = ClassicalRegister(5)    
        qc = QuantumCircuit(qr, cr)
        qc.h(0)
        qc.t(1)
        qc.x(2)
        qc.y(3)
        qc.z(4)
        qc.measure(qr, cr)
        
        qc2 = individual.to_qiskit_circuit()
        provider = SliQSimProvider()
        backend = provider.get_backend('sampling')
        job = execute(qc, backend=backend, shots=10000, optimization_level=0)
        job2 = execute(qc2, backend=backend, shots=10000, optimization_level=0)
        result = job.result()
        result2 = job2.result()
        p = normalize(result.get_counts(qc))
        q = normalize(result2.get_counts(qc2))
        dist = l2_distance(p, q)
        return dist
    
    fitness = Fitness(function=tmp_fitness_function)
    evolution_manager = EvolutionManager()
    circuit = evolution_manager.evolve_cgp(lambda_param=4, 
                                            gate_set=['h', 'x', 'y', 'z', 's', 't'],
                                            max_populations=10, 
                                            max_cols=1,
                                            max_rows=5,
                                            level_backs=1,
                                            fitness_function=fitness)
    
    fig = circuit.draw(output='mpl')
    fig.savefig('evolved_circuit.png')