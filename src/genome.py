import math
from gene import Gene
import copy
import random
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from typing import List
import time

class Genome:
    def __init__(self, gate_set=None, rows=10, cols=100):
        self.genes = []
        self.fitness = math.inf
        self.gate_set = gate_set
        self.cols = cols
        self.rows = rows
        self.col_to_num_of_multi_qubits = {} # mapping column index to number of multi-qubit gates in that column
        for i in range(cols):
            self.col_to_num_of_multi_qubits[i] = 1
            
        for i in range(rows * cols):
            gene = Gene(gate='empty')
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
        num_of_genes = self.rows * self.cols
        available_nodes_in_curr_col = [j for j in range(self.rows)]
        for i in range(num_of_genes):
            if i % self.rows == 0:
                available_nodes_in_curr_col = [j for j in range(self.rows)]
            
            if self.genes[i].gate != 'empty':
                continue
            
            
            curr_col = i // self.rows
            curr_row = i % self.rows
            multi_qubit_idx = self.col_to_num_of_multi_qubits[curr_col]
            max_skips = self.cols - curr_col - 1
            #max_skips = 1
            if max_skips < 0:
                max_skips = 0
            gene = Gene()
            chosen_gate = gene.random(gate_set=self.gate_set, max_qubit=self.rows, max_skips=max_skips)
            if chosen_gate.multi_qubit:
                self.col_to_num_of_multi_qubits[curr_col] += 1
                # multi-qubit gate, generate all its part and place them into random available rows
                if len(available_nodes_in_curr_col) < chosen_gate.qubits:
                    # not enough available nodes, place identity (SKIP[0])
                    gene.gate = 'SKIP'
                    gene.skips = 0
                    self.genes[i] = gene
                    available_nodes_in_curr_col.remove(curr_row)
                else:
                    # choose rows where to place it
                    rows_chosen = [curr_row]
                    available_nodes_in_curr_col.remove(curr_row)
                    rows_chosen += random.sample(available_nodes_in_curr_col, chosen_gate.qubits - 1)
                    available_nodes_in_curr_col.append(curr_row)
                    
                    for j in range(chosen_gate.qubits):
                        new_gene = Gene(gate=chosen_gate.name)
                        new_gene.gate = chosen_gate.name
                        new_gene.part = j
                        new_gene.multiqubit_idx = multi_qubit_idx
                        new_gene.skips = random.randint(0, max_skips)
                        random_row = random.choice(rows_chosen) 
                        index = random_row + curr_col * self.rows
                        self.genes[index] = new_gene
                        available_nodes_in_curr_col.remove(random_row)
                        rows_chosen.remove(random_row)
            else:
                # single-qubit gate
                self.genes[i] = gene
                available_nodes_in_curr_col.remove(curr_row)
            
            
            if curr_row == self.rows - 1:
                # reset the list of available nodes when going to the next column
                available_nodes_in_curr_col = [j for j in range(self.rows)]
                
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
    
    def mutate(self, logger=None):
        prob_change_gate = 1
        
        assert prob_change_gate == 1.0, "Mutation probabilities must sum to 1"        
        return self.mutate_change_gate(logger)

    def s_to_s_mutation(self, gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=None):
        if logger is not None:
            logger.log_s_to_s_mutation()
        #print(f"s_to_s_mutation on index {gene_to_mutate_idx} from {self.genes[gene_to_mutate_idx].gate} to {gate_to_mutate_to.name}")
        self.genes[gene_to_mutate_idx] = gene_to_mutate_to
        return self
    
    def m_to_s_mutation(self, gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=None):
        if logger is not None:
            logger.log_m_to_s_mutation()
        #print(f"m_to_s_mutation on index {gene_to_mutate_idx} from {self.genes[gene_to_mutate_idx].gate} to {gate_to_mutate_to.name}")
        # find all parts
        parts = self.find_all_gate_parts(gene_to_mutate_idx)
        self.s_to_s_mutation(gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=logger)
        for part in parts:
            # generate new random gene for each part
            gene = Gene()
            chosen_gate = gene.random(gate_set=self.gate_set, max_qubit=self.rows)
            if chosen_gate.name == self.genes[part].gate and logger is not None:
                logger.log_useless_mutation()
            
            if chosen_gate.multi_qubit:
                self.s_to_m_mutation(part, chosen_gate, gene, logger=logger)
            else:
                self.s_to_s_mutation(part, chosen_gate, gene, logger=logger)
            
        return self

    def s_to_m_mutation(self, gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=None):
        if logger is not None:
            logger.log_s_to_m_mutation()
        #print(f"s_to_m_mutation on index {gene_to_mutate_idx} from {self.genes[gene_to_mutate_idx].gate} to {gate_to_mutate_to.name}")
        parts = self.find_all_gate_parts(gene_to_mutate_idx)
        # generate all indexes where all other parts of the multi-qubit gate will be placed
        num_of_indexes = gate_to_mutate_to.qubits - 1
        # Exclude gene_to_mutate_idx row from selection
        available_rows = [row for row in range(self.rows) if row != (gene_to_mutate_idx % self.rows)]
        indexes = random.sample(available_rows, num_of_indexes)
        
        # generate multi_qubit_idx for all parts, generate new genes for all parts
        # and distribute them randomly to the indexes
        self.col_to_num_of_multi_qubits[gene_to_mutate_idx // self.rows] += 1
        multi_qubit_idx = self.col_to_num_of_multi_qubits[gene_to_mutate_idx // self.rows]
        gene_to_mutate_to.multiqubit_idx = multi_qubit_idx
        gene_to_mutate_to.part = 0
        gene_to_mutate_to.skips = random.randint(0, self.cols - (gene_to_mutate_idx // self.rows) - 1)
        #gene_to_mutate_to.skips = random.randint(0, 1)
        self.s_to_s_mutation(gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=logger)
    
        for i, index in enumerate(indexes):
            new_gene = Gene()
            new_gene.gate = gate_to_mutate_to.name
            new_gene.part = i + 1
            new_gene.multiqubit_idx = multi_qubit_idx
            new_gene.skips = random.randint(0, self.cols - (gene_to_mutate_idx // self.rows) - 1)
            #new_gene.skips = random.randint(0, 1)
            
            gene_to_mutate = self.genes[index + (gene_to_mutate_idx // self.rows) * self.rows]
            if new_gene.gate == gene_to_mutate.gate and logger is not None:
                logger.log_useless_mutation()
            
            if gene_to_mutate.part != -1:
                self.m_to_s_mutation(index + (gene_to_mutate_idx // self.rows) * self.rows, gate_to_mutate_to, new_gene, logger=logger)
            else:
                self.s_to_s_mutation(index + (gene_to_mutate_idx // self.rows) * self.rows, gate_to_mutate_to, new_gene, logger=logger)            
            
        # if the mutation was M -> M
        for part in parts:
            # generate new random gene for each part
            gene = Gene()
            chosen_gate = gene.random(gate_set=self.gate_set, max_qubit=self.rows)
            gene_to_mutate = self.genes[part]
            gene_to_mutate_multiqubit = gene_to_mutate.part != -1
            if chosen_gate.name == gene_to_mutate.gate and logger is not None:
                logger.log_useless_mutation()
            
            if gene_to_mutate_multiqubit:
                if chosen_gate.multi_qubit:
                    self.s_to_m_mutation(part, chosen_gate, gene, logger=logger)
                else:
                    self.m_to_s_mutation(part, chosen_gate, gene, logger=logger)
            else:
                if chosen_gate.multi_qubit:
                    self.s_to_m_mutation(part, chosen_gate, gene, logger=logger)
                else:
                    self.s_to_s_mutation(part, chosen_gate, gene, logger=logger)
                        
        return self
        
    def mutate_change_gate(self, logger=None):
        time_start = time.time()
        # if the mutation is changing single-qubit gate, then change the gate of a random gate
        # if the new gate is multi-qubit, generate all its parts on other random rows
        # if we destroyed multi-qubit gate by the new generating, re-generate its parts
        
        # if the mutation is changing multi-qubit gate, change all its parts
        #print(f"{self}")
        gene_to_mutate_idx = random.randint(0, len(self.genes) - 1)
        gene_to_mutate = self.genes[gene_to_mutate_idx]
        gate_to_mutate_to = random.choice(self.gate_set)
        mutating_multi_qubit = gene_to_mutate.part != -1
        mutating_to_multi_qubit = gate_to_mutate_to.multi_qubit
        gene_to_mutate_to = Gene(gate=gate_to_mutate_to.name)
        gene_to_mutate_to.skips = random.randint(0, self.cols - (gene_to_mutate_idx // self.rows) - 1)
        #gene_to_mutate_to.skips = random.randint(0, 1)
        gene_to_mutate_to.multiqubit_idx = 0
        gene_to_mutate_to.part = -1
        if gate_to_mutate_to.name == gene_to_mutate.gate and logger is not None:
            logger.log_useless_mutation()
        
        if not mutating_multi_qubit and not mutating_to_multi_qubit:
            
            # S -> S change
            # change the gate accordingly
            self.s_to_s_mutation(gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=logger)       
        elif mutating_multi_qubit and not mutating_to_multi_qubit:
            # M -> S
            # get all parts of the multi-qubit gate, change this one to the new gate
            # and call either S -> S if the part is being changed to a single-qubit gate
            # or call S -> M if the part is being changed to a multi-qubit gate
            self.m_to_s_mutation(gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=logger)
        else:          
            # S -> M
            # generate all indexes where the multi-qubit gate will be placed
            # and either call S -> S if the index under change is not part of a multi-qubit gate
            # or call M -> S if the index under change is part of a multi-qubit gate
              
            # M -> M
            # this is the same as S -> M ????
            # generate all indexes where the multi-qubit gate will be placed
            # for all parts:
            # and either call M -> S if the index under change is part of a multi-qubit gate
            # or call S -> S if the index under change is not part of a multi-qubit gate
            self.s_to_m_mutation(gene_to_mutate_idx, gate_to_mutate_to, gene_to_mutate_to, logger=logger)
        #print(f"Mutated genome: {self}")
        time_end = time.time()
        if logger is not None:
            logger.log_mutation(time_end - time_start)
        
        return self

    def __str__(self):
        string = f"Genome(fitness={self.fitness}, genes=["
        for gate in self.genes:
            string += "(" + str(gate) + "), "
        string += f"]"
        return string
    
    def find_all_gate_parts(self, index) -> List[int]:
        column = index // self.rows
        start = column * self.rows
        end = start + self.rows
        parts = []
        for k in range(start, end):
            if self.genes[k].part != -1 and self.genes[k].multiqubit_idx == self.genes[index].multiqubit_idx and k != index:
                parts.append(k)
        return parts
    
    def nodes_to_process(self):
        nodes_to_process = self.genes
        for gene in nodes_to_process:
            print(f"Node: {gene.gate}, Part: {gene.part}, Multiqubit Index: {gene.multiqubit_idx}, Skips: {gene.skips}")
        for i, node in enumerate(nodes_to_process):
            if node.gate != 'SKIP':
                continue
            else:
                nodes_to_process[i].active = False
                for j in range(node.skips):
                    index = i + (j+1) * self.rows
                    if index >= len(nodes_to_process):
                        break
                    
                    node_to_remove = nodes_to_process[i + (j+1)*self.rows]
                    if node_to_remove.part != -1:
                        # its a multi-qubit gate
                        multiqubit_idx = node_to_remove.multiqubit_idx
                        # find all nodes with the same multiqubit_idx in the column and set them to inactive
                        start = ((i + (j+1)*self.rows) // self.rows) * self.rows
                        end = start + self.rows
                        for k in range(start, end):
                            if nodes_to_process[k].part != -1 and nodes_to_process[k].multiqubit_idx == multiqubit_idx:
                                nodes_to_process[k].active = False
                        
                    else:
                        # its a single-qubit gate
                        node_to_remove.active = False
                    
        for i, node in enumerate(nodes_to_process):
            if node.active == True:
                print(f"Node {i} is active: {node}")
        return nodes_to_process

    def to_qiskit_circuit(self):
        """
        Convert the genome's genotype to Qiskit QuantumCircuit object
        for quantum circuit simulation
        SKIP 'gate' is used to skip a certain amount of columns in the circuit
        for higher variability of the circuit
        """
        qr = QuantumRegister(self.rows)
        cr = ClassicalRegister(self.rows)
        qc = QuantumCircuit(qr, cr)

        # https://quantumcomputing.stackexchange.com/questions/13677/qiskit-add-a-standard-gate-to-circuit-from-a-string        
        active_nodes = self.nodes_to_process()
        for i, node in enumerate(active_nodes):
            if node.active == False:
                continue
            qubit = i % self.rows
            column = i // self.rows
            if node.part == -1:
                # adding single-qubit gate
                getattr(qc, node.gate)(qubit)
                node.active = False
            else:
                # adding multi-qubit gate
                start = column * self.rows
                end = start + self.rows
                parts = []
                for k in range(start, end):
                    if active_nodes[k].part != -1 and active_nodes[k].multiqubit_idx == node.multiqubit_idx:
                        active_nodes[k].active = False
                        qubit = k % self.rows
                        index = active_nodes[k].part
                        if index >= len(parts):
                            parts.extend([0] * (index - len(parts) + 1))
                        parts[active_nodes[k].part] = qubit
                getattr(qc, node.gate)(*parts)
        # Add measurement to all qubits
        # qc.measure(qr, cr)
        
        for node in self.genes:
            node.active = True
        
        return qc

    def to_qasm(self) -> str:
        active_nodes = self.nodes_to_process()
        qasm_str = "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[{}];\ncreg c[{}];\n".format(self.rows, self.rows)
        for i, node in enumerate(active_nodes):
            if node.active == False:
                continue
            qubit = i % self.rows
            column = i // self.rows
            if node.part == -1:
                # adding single-qubit gate
                qasm_str += "{} q[{}];\n".format(node.gate, qubit)
                node.active = False
            else:
                # adding multi-qubit gate
                start = column * self.rows
                end = start + self.rows
                parts = []
                for k in range(start, end):
                    if active_nodes[k].part != -1 and active_nodes[k].multiqubit_idx == node.multiqubit_idx:
                        active_nodes[k].active = False
                        qubit = k % self.rows
                        index = active_nodes[k].part
                        if index >= len(parts):
                            parts.extend([0] * (index - len(parts) + 1))
                        parts[active_nodes[k].part] = qubit
                qasm_str += "{} {};\n".format(node.gate, ', '.join(f"q[{i}]" for i in parts))
                
        for node in self.genes:
            node.active = True
        return qasm_str