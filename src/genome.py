import math
from gene import Gene
import copy
import random
from typing import List
import time
from logger import Logger
from gate import GateSet

class Genome:
    def __init__(self, gate_set : GateSet, qubits : int, operations : int, max_qubits_needed : int) -> None:
        self.genes = []
        self.fitness = math.inf
        self.gate_set = gate_set
        self.qubits = qubits
        self.operations = operations
        self.max_qubits_needed = max_qubits_needed
        self.actives_mutated = 0
        self.first_evaluation = True

    def __deepcopy__(self, memo_dict : dict) -> "Genome":
        genome = Genome(gate_set=self.gate_set, qubits=self.qubits, operations=self.operations, max_qubits_needed=self.max_qubits_needed)
        genome.genes = [copy.deepcopy(gene) for gene in self.genes]
        return genome

    
    def generate_random_individual(self) -> "Genome": 
        for i in range(self.operations):
            #max_skips = self.operations - i - 1
            max_skips = 10
            gene = Gene()
            gene.random(gate_set=self.gate_set.get_gates(), max_qubits_needed=self.max_qubits_needed, max_qubit=self.qubits, max_skips=max_skips)
            self.genes.append(gene)
        return self
    
    def print_genome(self) -> None:
        print("Genome:")
        for gene in self.genes:
            print(f"Gene: {gene.gate}, Parts: {gene.parts}, Skips: {gene.skips}, Active: {gene.active}")
        print(f"Fitness: {self.fitness}")

    def mutate_gene(self, gene: Gene, logger : Logger) -> None:
        prob_change_gate = 0.4
        prob_change_indice = 0.1
        prob_change_skips = 0.4
        prob_swap_operations = 0.1
        total_prob = prob_change_gate + prob_change_indice + prob_change_skips + prob_swap_operations
        assert (total_prob - 1) < 1e-6
        
        prob = random.uniform(0, 1)
        if prob < prob_change_gate:
            chosen_gate = random.choice(self.gate_set.get_gates())
            if chosen_gate.name == gene.gate:
                logger.log_useless_mutation()
            gene.gate = chosen_gate.name
            if gene.gate in ['cx', 'x'] and gene.parts[-1] != self.qubits-1:
                parts = [x for x in gene.parts if x != self.qubits-1]
                gene.parts = random.sample(parts, len(parts)) + [self.qubits-1]

        elif prob < prob_change_gate + prob_change_indice:
            excluded_indices = list(set(range(self.qubits)) - set(gene.parts))
            if len(excluded_indices) == 0:
                # no indices can be used, swap two that are already in the gene
                if gene.gate == 'cx' and gene.parts[-1] == self.qubits-1:
                    #TODO RUS specific: if the gate is cx and the target is the non-ancilla,
                    # we cant make any swap
                    return
        
                index_to_swap_1 = random.randint(0, len(gene.parts) - 1)
                index_to_swap_2 = random.randint(0, len(gene.parts) - 1)
                gene.parts[index_to_swap_1], gene.parts[index_to_swap_2] = gene.parts[index_to_swap_2], gene.parts[index_to_swap_1]
            else:
                chosen_index = random.choice(excluded_indices)
                index_to_change = random.randint(0, len(gene.parts) - 1)
                #TODO RUS specific: if the gate is cx or x and the index to change is 0,
                # in x, we can just return, in cx, swap the control, not the target
                if index_to_change == self.qubits-1:
                    if gene.gate == 'x':
                        return
                    elif gene.gate == 'cx':
                        index_to_change = random.randint(0, len(gene.parts) - 2)


                if gene.parts[index_to_change] == chosen_index:
                    logger.log_useless_mutation()
                gene.parts[index_to_change] = chosen_index
        elif prob < prob_change_gate + prob_change_indice + prob_change_skips:
            #max_skips = self.operations - self.genes.index(gene) - 1
            max_skips = 10

            skips = random.randint(0, max_skips)
            if skips == gene.skips:
                logger.log_useless_mutation()
            gene.skips = skips
        else:
            gene_to_swap_with = random.choice(self.genes)
            if gene_to_swap_with == gene:
                logger.log_useless_mutation()
                return
            else:
                index_to_swap = self.genes.index(gene_to_swap_with)
                self.genes[index_to_swap] = copy.deepcopy(gene)
                self.genes[self.genes.index(gene)] = copy.deepcopy(gene_to_swap_with)


    def mutate(self, logger : Logger, active_mut_rate : float, inactive_mut_rate : float) -> "Genome":
        time_start = time.time()
        
        self.actives_mutated = 0
        i = 0
        in_actives = True
        inactives_end = 0
        while i < len(self.genes):
            gene = self.genes[i]
            prob = random.uniform(0, 1)
            if i > inactives_end:
                in_actives = True
                inactives_end = 0
        
            if gene.gate == 'SKIP':
                in_actives = False
                inactives_end = i + gene.skips + 1
            
            if in_actives and prob < active_mut_rate:
                # mutate active gene
                self.mutate_gene(gene, logger)
                self.actives_mutated += 1
            elif not in_actives and prob < inactive_mut_rate:
                # mutate inactive gene
                self.mutate_gene(gene, logger)
            i += 1
        time_end = time.time()
        logger.log_mutation(time_end - time_start)
        return self

    def __str__(self) -> str:
        string = f"Genome(fitness={self.fitness}, genes=["
        for i, gate in enumerate(self.genes):
            string += "(" + str(gate) + ")"
            string += "; " if i != len(self.genes) - 1 else ""
        string += "])"
        return string
    
    def set_genes(self, genes: List[Gene]) -> None:
        self.genes = genes

    def to_qasm(self) -> tuple[str, int]:
        number_of_gates = 0
        qasm_str = "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[{}];\ncreg c[{}];\n".format(self.qubits, self.qubits)
        i = 0
        while i < len(self.genes):
            gene = self.genes[i]
            if gene.gate == 'SKIP':
                i += gene.skips + 1
                continue
            else:
                gate = next((g for g in self.gate_set.get_gates() if g.name == gene.gate), None)
                j = 0
                number_of_gates += 1
                qasm_str += f"{gate.name} "
                while j < gate.qubits:
                    qasm_str += f"q[{gene.parts[j]}], "
                    j += 1
                qasm_str = qasm_str[:-2] + ";\n"
                i += 1
        return qasm_str, number_of_gates

    def to_qasm_no_newlines(self) -> str:
        qasm_str = "OPENQASM 2.0;include \"qelib1.inc\";qreg q[{}];creg c[{}];".format(self.qubits, self.qubits)
        i = 0
        while i < len(self.genes):
            gene = self.genes[i]
            if gene.gate == 'SKIP':
                i += gene.skips + 1
                continue
            else:
                gate = next((g for g in self.gate_set.get_gates() if g.name == gene.gate), None)
                j = 0
                qasm_str += f"{gate.name} "
                while j < gate.qubits:
                    qasm_str += f"q[{gene.parts[j]}], "
                    j += 1
                qasm_str = qasm_str[:-2] + ";"
                i += 1
        return qasm_str
    
    def check_fitness_eval(self) -> bool:
        return False if self.first_evaluation or self.actives_mutated == 0 else True
    
    def first_evaluation_done(self) -> None:
        self.first_evaluation = False

    def __hash__(self) -> int:
        hash = 0
        for gene in self.genes:
            hash += hash(gene)
        return hash

    @staticmethod
    def from_string(genome_str : str) -> "Genome":
        """
        Genome(fitness=50.0, genes=[(tdg [1, 0] 8 True); (t [0, 1] 8 True); (t [1, 0] 7 True); (cx [1, 0] 5 True);])
        """
        genes = []
        max_qubits = 0

        # first find fitness
        eq_index = genome_str.find('=')
        first_sep_index = genome_str.find(',')
        fitness_str = genome_str[eq_index+1:first_sep_index]
        fitness = float(fitness_str)

        # rests of the string are all genes
        genome_str = genome_str[first_sep_index+1:]
        genes_str = genome_str.split(';')
        for gene_str in genes_str:
            left_bracket_index = gene_str.find('(')
            right_bracket_index = gene_str.find(')')
            gene_str = gene_str[left_bracket_index+1:right_bracket_index]

            # first get the gate name
            first_space = gene_str.find(' ')
            gate_str = gene_str[:first_space]
            gene_str = gene_str[first_space+1:]

            # then parse all qubits in [q0, q1 ...]
            left_bracket_index = gene_str.find('[')
            right_bracket_index = gene_str.find(']')
            qubits_str = gene_str[left_bracket_index+1:right_bracket_index]

            qubits = [int(qubit) for qubit in qubits_str.split(',')]
        
            if max(qubits) > max_qubits:
                max_qubits = max(qubits)
            
            gene_str = gene_str[right_bracket_index+2:]
            #after that, parse the skips number and activity flag
            space_index = gene_str.find(' ')
            skips_str = gene_str[:space_index]
            skips = int(skips_str)
            gene_str = gene_str[space_index+1:]

            # then parse the active flag
            active_str = gene_str[right_bracket_index+1:]
            active = active_str == 'True'

            gene = Gene()
            gene.gate = gate_str
            gene.parts = qubits
            gene.skips = skips
            gene.active = active
            genes.append(gene)
        
        max_qubits_needed = len(genes[0].parts)
        
        # string representation cant infer the gate set, since the string contains all generated qubits,
        # not only the ones used by the specific gate
        genome = Genome(gate_set=GateSet(preset='default'), qubits=max_qubits+1, operations=len(genes), max_qubits_needed=max_qubits_needed)
        genome.fitness = fitness
        genome.genes = genes
        return genome