from genome import Genome
from fitness import Fitness
import multiprocessing
import subprocess
import fcntl
from logger import Logger
import numpy as np
import time
import os
import mqt.core
import mqt.ddsim
from concurrent.futures import ThreadPoolExecutor



class MultiThreadedFitnessEvaluator:
    def __init__(self, fitness_function : Fitness, logger : Logger) -> None:
        """
            Initialize fitness function evaluator,
            boot up the simulator in persistent mode waiting
            for jobs to arrive into a queue (evaluation done in a thread pool)
        """
        self.fitness_function = fitness_function
        self.simulator_name = self.fitness_function.get_name()
        if self.simulator_name == 'sliqsim':
            self.simulator = subprocess.Popen(['./SliQSim'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elif self.simulator_name == 'ddsim':
            self.simulator = ThreadPoolExecutor()
            #self.simulator = subprocess.Popen(['./ddsim'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.genome_map = {}
        self.lowest_id = 0
        self.circuits_sent = 0
        self.fittest = None
        self.logger = logger

    def add_genome(self, genome : Genome) -> None:
        """
            Create a ID for a specified genome and add it to the genome map
            ID : Genome
            after fitness evaluation, retreive the genome by ID and update its fitness
        """
        self.genome_map[self.lowest_id] = genome
        self.lowest_id += 1

    def reset(self) -> None:
        self.genome_map = {}
        self.lowest_id = 0
        self.circuits_sent = 0
        self.fittest = None

    def write_to_stdin(self, xml : str) -> None:
        try:
            while(len(xml) > self.get_pipe_size()):
                self.simulator.stdin.write(xml[:self.get_pipe_size()])
                self.simulator.stdin.flush()
                xml = xml[self.get_pipe_size():]
            self.simulator.stdin.write(xml)
            self.simulator.stdin.flush()
        except Exception as e:
            print(f"Error writing to stdin: {e}")


    def get_genome(self, id : int) -> Genome:
        return self.genome_map[id]

    @staticmethod
    def parse_statevector(config : str, basis_state : str) -> np.array:
        start = '<statevector_' + basis_state + '>'
        end = '</statevector_' + basis_state + '>'
        statevector_start = config.find(start) + len(start)
        statevector_end = config.find(end)
        statevector_str = config[statevector_start+1:statevector_end-1]

        statevector = []
        for element in statevector_str.split(','):
            element = complex(element)
            statevector.append(element)
        return np.array(statevector)

    @staticmethod
    def parse_id(config : str) -> int:
        id_start = config.find('<id>') + len('<id>')
        id_end = config.find('</id>')
        return int(config[id_start:id_end])

    @staticmethod
    def parse_matrix(config : str) -> np.array:
        matrix_start = config.find('<matrix>') + len('<matrix>')
        matrix_end = config.find('</matrix>')
        matrix = np.array(config[matrix_start+1:matrix_end-1].split(','))
        return matrix

    def parse_sliqsim_config(self, config : str) -> tuple[int, list[np.array]]:
        """
            Parse the config from the simulator
            Return the ID, statevector for basis state |0>, statevector for basis state |1> on the non-ancilla qubit
            all ancilla qubits are in the |0> state
        """
        id = self.parse_id(config)

        statevector_0 = self.parse_statevector(config, '0')
        statevector_1 = self.parse_statevector(config, '1')
        statevector_plus = self.parse_statevector(config, 'plus')
        statevector_minus = self.parse_statevector(config, 'minus')

        return id, [statevector_0, statevector_1, statevector_plus, statevector_minus]


    def parse_ddsim_matrix(self, matrix_str : str) -> np.array:
        matrix = []
        for line in matrix_str.split('\n'):
            if line.startswith('['):
                elements = [x.strip() for x in line.strip('[]').split(',') if x.strip()]
                row = []
                for elem in elements:
                    try:
                        row.append(complex(elem))
                    except ValueError:
                        row.append(0j)
                matrix.append(row)
        return matrix

    def parse_ddsim_config(self, config : str) -> tuple[int, np.array]:
        """
            Parse the config from the simulator
            Return the ID, matrix
        """
        id = self.parse_id(config=config)
        matrix_start = config.find('<matrix>') + len('<matrix>')
        matrix_end = config.find('</matrix>')
        matrix = self.parse_ddsim_matrix(config[matrix_start+1:matrix_end-1])
        return id, matrix
        
    def read_config(self) -> str:
        config = ''
        while '</xml>' not in config:
            line = self.simulator.stdout.readline()
            if not line:
                continue
            config += line
        return config

    def read_results(self) -> Genome:
        """
            Wait until the simulator writes the output configs for all IDs passed into it
            Example config:
                <xml><id>0</id><statevector_0>[1+0j, 0+0j]</statevector_0><statevector_1>[0+0j, 1+0j]</statevector_1></xml>
            After reading the config, project the statevectors so that all ancilla bits are measured as 0
            Projected vectors are then compared to the target statevectors with Euclidean distance
            And the fitness is the average of the distances
        """
        ids_found = 0
        while(ids_found < self.circuits_sent):
            config = self.read_config()
            id, statevectors = self.parse_sliqsim_config(config)
            genome = self.get_genome(id)
            genome.fitness = self.fitness_function.evaluate(genome, statevectors, self.logger)
            if self.fittest is None or genome.fitness < self.fittest.fitness:
                self.fittest = genome
            ids_found += 1
        return self.fittest

    def get_pipe_size(self) -> int:
        return fcntl.fcntl(self.simulator.stdin, fcntl.F_GETPIPE_SZ)

    def genome_to_xml(self, genome : Genome) -> str:
        xml = '<xml><id>' + str(self.lowest_id) + '</id>'
        xml += '<qasm>' + genome.to_qasm_no_newlines() + '</qasm>'
        xml += '</xml>\n'
        self.add_genome(genome)
        return xml

    def read_batch(self, batch : list[Genome]) -> None:
        received = 0
        fittest = None
        while(received < len(batch)):
            config = self.read_config()
            if self.simulator_name == 'sliqsim':
                id, statevectors = self.parse_sliqsim_config(config)
                genome = self.get_genome(id)
                genome.fitness = self.fitness_function.evaluate(individual=genome, statevectors=statevectors, logger=self.logger)

            if fittest is None or genome.fitness < fittest.fitness:
                fittest = genome
            received += 1
        return fittest
    

    def worker_work(self, individual : Genome) -> float:
        qasm, number_of_gates = individual.to_qasm()
        # empty qasm file causes segfault
        if number_of_gates == 0:
            individual.fitness = 1.0
            return individual.fitness

        qc = mqt.core.QuantumComputation().from_qasm_str(qasm)
        sim = mqt.ddsim.UnitarySimulator(qc)
        sim.construct()
        dd = sim.get_constructed_dd()
        matrix = np.array(dd.get_matrix(individual.qubits), copy=False)
        individual.fitness = self.fitness_function.evaluate(individual=individual, matrix=matrix, logger=self.logger)
        return individual.fitness

    def evaluate(self, population : "Population") -> Genome:
        self.fittest = population.fittest
        time_start = time.time()
        batch_size = os.cpu_count()
        fittest = None
        if self.simulator_name == 'sliqsim':
            for i in range(0, len(population.individuals), batch_size):
                batch = population.individuals[i:i+batch_size]
                for genome in batch:
                    conversion_start = time.time()
                    xml = self.genome_to_xml(genome)
                    conversion_end = time.time()
                    self.logger.log_conversion(conversion_end - conversion_start)

                    self.write_to_stdin(xml)
                    self.logger.log(type='INFO', message=f"Sent circuit {self.circuits_sent} to simulator")
                    self.circuits_sent += 1
                batch_fittest = self.read_batch(batch)
                if fittest is None or batch_fittest.fitness < fittest.fitness:
                    fittest = batch_fittest
        elif self.simulator_name == 'ddsim':
            results = self.simulator.map(self.worker_work, population.individuals)
            for i, result in enumerate(results):
                self.logger.log(type='DEBUG', message=f"Fitness {result} for individual {population.individuals[i]}")
                if fittest is None or result < fittest.fitness:
                    fittest = population.individuals[i]

        time_end = time.time()
        self.logger.log_fitness_call(time_end - time_start)

        self.reset()
        return fittest

    def gracefully_terminate_simulator(self) -> None:
        xml = '<xml><flag>terminate</flag></xml>'
        self.write_to_stdin(xml)
        self.simulator.stdin.flush()
        self.simulator.terminate()
        self.simulator.wait()
        self.simulator.stdout.close()
        self.simulator.stdin.close()
        self.simulator.stderr.close()