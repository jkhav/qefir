from genome import Genome
from fitness import Fitness
import subprocess
import fcntl
from logger import Logger
import numpy as np
import time

class MultiThreadedFitnessEvaluator:
    def __init__(self, fitness_function : Fitness) -> None:
        """
            Initialize fitness function evaluator,
            boot up the simulator SliQSim
        """
        self.fitness_function = fitness_function
        self.simulator = subprocess.Popen(['./SliQSim'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.genome_map = {}
        self.lowest_id = 0
        self.circuits_sent = 0
        self.fittest = None

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
        while(len(xml) > self.get_pipe_size()):
            self.simulator.stdin.write(xml[:self.get_pipe_size()])
            self.simulator.stdin.flush()
            xml = xml[self.get_pipe_size():]
        self.simulator.stdin.write(xml)
        self.simulator.stdin.flush()


    def get_genome(self, id : int) -> Genome:
        return self.genome_map[id]

    def parse_statevector(self, statevector_str : str) -> np.array:
        statevector = []
        for element in statevector_str.split(','):
            element = complex(element)
            statevector.append(element)
        return np.array(statevector)

    def parse_config(self, config : str) -> tuple[int, np.array, np.array, np.array, np.array]:
        """
            Parse the config from the simulator
            Return the ID, statevector for basis state |0>, statevector for basis state |1> on the non-ancilla qubit
            all ancilla qubits are in the |0> state
        """
        id_start = config.find('<id>') + len('<id>')
        id_end = config.find('</id>')
        id = int(config[id_start:id_end])

        statevector_0_start = config.find('<statevector_0>') + len('<statevector_0>')
        statevector_0_end = config.find('</statevector_0>')
        statevector_0 = self.parse_statevector(config[statevector_0_start+1:statevector_0_end-1])


        statevector_1_start = config.find('<statevector_1>') + len('<statevector_1>')
        statevector_1_end = config.find('</statevector_1>')
        statevector_1 = self.parse_statevector(config[statevector_1_start+1:statevector_1_end-1])

        statevector_plus_start = config.find('<statevector_plus>') + len('<statevector_plus>')
        statevector_plus_end = config.find('</statevector_plus>')
        statevector_plus = self.parse_statevector(config[statevector_plus_start+1:statevector_plus_end-1])

        statevector_minus_start = config.find('<statevector_minus>') + len('<statevector_minus>')
        statevector_minus_end = config.find('</statevector_minus>')
        statevector_minus = self.parse_statevector(config[statevector_minus_start+1:statevector_minus_end-1])

        return id, statevector_0, statevector_1, statevector_plus, statevector_minus

    def read_config(self) -> str:
        config = ''
        while '</xml>' not in config:
            line = self.simulator.stdout.readline()
            if not line:
                continue
            config += line
        return config

    def read_results(self, logger : Logger) -> Genome:
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
            id, statevector_0, statevector_1, statevector_plus, statevector_minus = self.parse_config(config)
            genome = self.get_genome(id)
            genome.fitness = self.fitness_function.evaluate(genome, statevector_0, statevector_1, statevector_plus, statevector_minus, logger)
            if self.fittest is None or genome.fitness < self.fittest.fitness:
                self.fittest = genome
            #logger.log(type="DEBUG", message=f"Evaluated fitness for individual {genome} with fitness {genome.fitness}")
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

    def evaluate(self, population : "Population", logger : Logger) -> Genome:
        self.fittest = population.fittest
        time_start = time.time()
        for genome in population.individuals:
            conversion_start = time.time()
            xml = self.genome_to_xml(genome)
            conversion_end = time.time()
            logger.log_conversion(conversion_end - conversion_start)

            self.write_to_stdin(xml)
            self.circuits_sent += 1
        # after passing all genomes to be evaluated, wait for all the results
        fittest = self.read_results(logger)
        time_end = time.time()
        logger.log_fitness_call(time_end - time_start)

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