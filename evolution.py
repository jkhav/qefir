from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit_sliqsim_provider import SliQSimProvider
import random
import numpy
import datetime
import math
import copy
from typing import List

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

class Gate:
    def __init__(self, name='', qubits=1, parameter=0.0):
        self.name = name
        self.qubits = qubits
        self.parameter = parameter
        self.multi_qubit = qubits > 1
        self.multi_qubit_idx = 0


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
        self.active = False
        self.skips = 0
        self.idx = 0
        
    def random(self, gate_set=None, max_qubit=2, parameter_range = (-numpy.pi, numpy.pi), max_skips=0):
        self.gate = random.choice(gate_set)
        self.target_qubit = random.randint(0, max_qubit - 1)
        self.skips = random.randint(0, max_skips)
        self.idx = 0

    def print_gene(self):
        print(f"Gate: {self.gate}, Target: {self.target_qubit}")

    def __str__(self):
        return f"{self.gate}[{self.target_qubit}]"
        


class Genome:
    def __init__(self, mut_prob=0.7, gates=None, gate_set=None, max_qubits=10, max_depth=100):
        self.genes = []
        self.fitness = math.inf
        self.mutation_prob = mut_prob # in CGP, mutation is 1.0
        self.gate_set = gate_set
        self.gate_set += ['SKIP']
        self.gates = gates
        self.max_depth = max_depth
        self.max_qubits = max_qubits
        self.curr_cols = 0
        self.curr_rows = 0
        self.col_to_num_of_multi_qubits = {} # mapping column index to number of multi-qubit gates in that column
        for i in range(max_depth):
            self.col_to_num_of_multi_qubits[i] = 1
            
        for i in range(max_qubits * max_depth):
            gene = Gene(gate='')
            self.genes.append(gene)
        
    def copy(self):
        return copy.deepcopy(self)
    
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
        for i in range(num_of_genes):
            if self.genes[i].gate != '':
                continue
            curr_col = i // self.curr_rows
            curr_row = i % self.curr_rows
            multi_qubit_idx = self.col_to_num_of_multi_qubits[curr_col]
            max_skips = self.max_depth - curr_col - 1
            if max_skips < 0:
                max_skips = 0
            gene = Gene()
            gene.random(gate_set=self.gate_set, max_qubit=self.max_qubits, max_skips=max_skips)
            # if the gate is multi-qubit, generate all its parts (based on self.gates information about number of qubits of the gate)
            # the name of the gate is nameX where X is the number of the part
            if gene.gate == 'SKIP':
                print(f"Gene {i} is SKIP, skipping generation")
                self.genes[i] = gene
                continue
            # generate gate
            gate = random.choice(self.gates)
            print(f"Generating gene {i}: {gate.name} with qubits {gate.qubits} at column {curr_col}, row {curr_row}")
            if gate.multi_qubit:
                print("Generating multi-qubit gate")
                available_nodes_in_col_idxs = []
                print(f"Current column: {curr_col}, current row: {curr_row}, curr_rows: {self.curr_rows}")
                for j in range(self.curr_rows - curr_row):
                    print(f"Checking gene at index {curr_col * self.curr_rows + curr_row + j} in column {curr_col}, j={j}")
                    if self.genes[curr_col * self.curr_rows + curr_row + j].gate == '':
                        available_nodes_in_col_idxs.append(curr_col * self.curr_rows + curr_row + j)
                        
                print(f"Available nodes in column {curr_col}: {available_nodes_in_col_idxs}")
                if len(available_nodes_in_col_idxs) < gate.qubits:
                    # if there are not enough available nodes in the column, skip this gene
                    gene.gate = 'SKIP'
                    gene.target_qubit = 0
                    gene.active = False
                    self.genes[i] = gene
                    continue
                else:
                    # there are enough available nodes, generate all parts randomly in the available indexes
                    # one of them has to be on the current row
                    to_generate = [f"{gate.name}{j}" for j in range(gate.qubits)]
                    first_generated = random.choice(to_generate)
                    to_generate.remove(first_generated)
                    available_nodes_in_col_idxs.remove(curr_col * self.curr_rows + curr_row)
                    gene.gate = first_generated
                    gene.target_qubit = curr_row
                    gene.active = True
                    gene.idx = multi_qubit_idx
                    self.genes[i] = gene
                    
                    # now generate the rest
                    for j in range(gate.qubits - 1):
                        idx = random.choice(available_nodes_in_col_idxs)
                        available_nodes_in_col_idxs.remove(idx)
                        part = random.choice(to_generate)
                        to_generate.remove(part)
                        gene = Gene(gate=part, target=idx % self.curr_rows)
                        gene.idx = multi_qubit_idx
                        self.genes[idx] = gene
                    self.col_to_num_of_multi_qubits[curr_col] += 1
            else:
                gene.gate = gate.name
                gene.target_qubit = curr_row
                gene.active = True
                self.genes[i] = gene
    
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
        
        assert prob_change_gate == 1.0, "Mutation probabilities must sum to 1"        
        return self.mutate_change_gate()

    def mutate_change_gate(self):
        # if the mutation is changing single-qubit gate, then change the gate of a random gate
        # if the new gate is multi-qubit, generate all its parts on other random rows
        # if we destroyed multi-qubit gate by the new generating, re-generate its parts
        
        # if the mutation is changing multi-qubit gate, change all its parts
        
        #gene = random.choice(self.genes)
        #gene.gate = random.choice(self.gate_set)
        
        gene_to_mutate = random.choice(self.genes)
        multi_qubit = gene_to_mutate.idx != 0
        if multi_qubit:
            pass
        else:
            pass
        
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
        TODO this does not support multi-qubit gates yet
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
            gene = self.genes[i]
            if gene.active == False:
                i += 1
                continue
            
            
            if gene.gate == 'SKIP':
                # skip next N gates in self.genes
                # deactivate genes that come after it (in a row)
                # if deactivating a multi-qubit gate, deactivate all its parts
                skips = gene.skips
                step = self.curr_rows
                
                for j in range(skips):
                    if i + j * step < len(self.genes):
                        self.genes[i + j * step].active = False
                        if self.genes[i + j * step].idx != 0: # its a multi-qubit gate
                            # find all parts in the respective column
                            column_idx = (i + j * step) // self.curr_rows
                            for k in range(self.curr_rows):
                                if self.genes[column_idx * self.curr_rows + k].idx == self.genes[i + j * step].idx:
                                    self.genes[column_idx * self.curr_rows + k].active = False
            else:                
                digit_is_last = gene.gate[-1].isdigit()
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
                else:
                    if digit_is_last:
                        # multi-qubit gate
                        curr_column = i // self.curr_rows
                        name = gene.gate[:-1]  # remove the last digit
                        target_qubit = -1
                        controls = []
                        for j in range(self.curr_rows):
                            # 0 at the end is target, others are controls
                            curr_gene = self.genes[curr_column * self.curr_rows + j]
                            if curr_gene.idx == gene.idx:
                                digit = curr_gene.gate[-1]
                                if digit == '0':
                                    target_qubit = curr_gene.target_qubit
                                else:
                                    controls.append(curr_gene.target_qubit)
                        if name == 'cx':
                            qc.cx(controls[0], target_qubit)
                                
            i += 1
        # Add measurement to all qubits
        qc.measure(qr, cr)
        return qc
                

class Population:
    def __init__(self, fitness_function=Fitness()):
        self.individuals = [] # genomes in the population
        self.fittest =  None
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
            individual = Genome(gate_set=gate_set, gates=gates, max_qubits=max_qubits, max_depth=max_depth).generate_random_individual()
            print(f"Generated individual: {individual}")
            self.add_individual(individual)
        
        return self




class EvolutionManager:
    def __init__(self):
        self.logger = Logger()
    
    def initialize(self, lambda_param, gate_set, max_populations, fitness_function, qubits=2):
        """
        Initialize the evolution manager with parameters for CGP
        """
        self.gate_set = []
        for gate in gate_set:
            if not isinstance(gate, Gate):
                raise ValueError(f"Gate {gate} is not an instance of Gate class")
            
            if gate.qubits > 1:
                for i in range(gate.qubits):
                    self.gate_set += [f"{gate.name}{i}"]
            else:
                self.gate_set += [gate.name]
        
        self.gates = gate_set
        self.lambda_param = lambda_param
        self.gate_set += ['SKIP']
        self.max_populations = max_populations
        self.fitness_function = fitness_function
        self.population = Population(fitness_function=fitness_function) if fitness_function is not None else Population(fitness_function=Fitness())
        self.fittest = None
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
            individual = fittest.copy() 
            individual.mutate()
            new_population.add_individual(individual)
        
        new_population.evaluate_fitness()
        for individual in self.population.individuals:
            self.logger.log(type='DEBUG', message=f"Mutated individual: {individual}")
        
        
        self.fittest = new_population.select_fittest()
        self.logger.log(type='INFO', message=f"Population {self.curr_population + 1} evaluated. Fittest fitness: {self.fittest.fitness}")
        
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
                                                                    gates=self.gates,
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
        def bhattaharyya_dst(p, q):
            keys = set(p) | set(q)
            print("Calculating Bhattacharyya distance for:")
            print(f"p: {p}")
            print(f"q: {q}")
            bc = 0.0
            for k in keys:
                bc += math.sqrt(p.get(k, 0) * q.get(k, 0))
            if bc == 0:
                return 1.0
            else:
                d = -math.log(bc)
                return d
        
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
        dist = bhattaharyya_dst(p, q)
        return dist
    
    
    hadamard = Gate(name='h', qubits=1, parameter=0.0)
    x = Gate(name='x', qubits=1, parameter=0.0)
    y = Gate(name='y', qubits=1, parameter=0.0)
    z = Gate(name='z', qubits=1, parameter=0.0)
    s = Gate(name='s', qubits=1, parameter=0.0)
    t = Gate(name='t', qubits=1, parameter=0.0)
    cnot = Gate(name='cx', qubits=2, parameter=0.0)
    gate_set = [hadamard, x, y, z, s, t, cnot]
    
    fitness = Fitness(function=tmp_fitness_function)
    evolution_manager = EvolutionManager()
    circuit = evolution_manager.evolve_cgp(lambda_param=4, 
                                            gate_set=gate_set,
                                            max_populations=1000, 
                                            max_cols=1,
                                            max_rows=5,
                                            level_backs=1,
                                            fitness_function=fitness)
    
    fig = circuit.draw(output='mpl')
    fig.savefig('evolved_circuit.png')