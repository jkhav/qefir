import sys
import math
import evolution as evo
import numpy as np
import subprocess
import time
from logger import Logger
import quantum_gates as qg
from genome import Genome
from gate import Gate

if __name__ == "__main__":
    gate_set = evo.GateSet(preset='default')
    fitness = evo.Fitness(name='ddsim')
    evolution_manager = evo.EvolutionManager()
    evolution_manager.initialize(
                                gate_set=gate_set,
                                max_populations=50, 
                                max_operations=20,
                                fitness_function=fitness,
                                max_qubits=2,
                                active_mut_rate=0.03,
                                inactive_mut_rate=0.06,
                                crossover_rate=0.7,
                                population_size=100,
                                allowed_err=1e-10,
                                crossover_method='OnePointCrossover',
                                selection_method='TournamentSelection',
                                tournament_size=2
                                )
    circuit = evolution_manager.evolve()
    qasm_str, _ = circuit.to_qasm()
    print("Final circuit QASM:")
    print(qasm_str)
    
    # save it into a file
    with open('final_circuit.qasm', 'w') as f:
        f.write(qasm_str)