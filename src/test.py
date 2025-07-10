import sys
import math
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit_sliqsim_provider import SliQSimProvider
import evolution as evo

if __name__ == "__main__":
    def tmp_fitness_function(individual):   
        # allowed error 
        allowed_err = 0.001
        
        def bhattaharyya_dst(p, q):
            keys = set(p) | set(q)
            #print("Calculating Bhattacharyya distance for:")
            #print(f"p: {p}")
            #print(f"q: {q}")
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
        job = execute(qc, backend=backend, shots=2048, optimization_level=0)
        job2 = execute(qc2, backend=backend, shots=2048, optimization_level=0)
        result = job.result()
        result2 = job2.result()
        p = normalize(result.get_counts(qc))
        q = normalize(result2.get_counts(qc2))
        dist = bhattaharyya_dst(p, q)
        
        #if dist < allowed_err:
        #    dist = 0.0
        
        return dist
    
    
    hadamard = evo.Gate(name='h', qubits=1, parameter=0.0)
    x = evo.Gate(name='x', qubits=1, parameter=0.0)
    y = evo.Gate(name='y', qubits=1, parameter=0.0)
    z = evo.Gate(name='z', qubits=1, parameter=0.0)
    s = evo.Gate(name='s', qubits=1, parameter=0.0)
    t = evo.Gate(name='t', qubits=1, parameter=0.0)
    cnot = evo.Gate(name='cx', qubits=2, parameter=0.0)
    gate_set = [hadamard, x, y, z, s, t, cnot]
    gate_set2 = [cnot]
    
    fitness = evo.Fitness(function=tmp_fitness_function)
    evolution_manager = evo.EvolutionManager()
    circuit = evolution_manager.evolve_cgp(lambda_param=4, 
                                            gate_set=gate_set2,
                                            max_populations=1000, 
                                            max_cols=10,
                                            max_rows=5,
                                            level_backs=1,
                                            fitness_function=fitness)
    
    fig = circuit.draw(output='mpl')
    fig.savefig('evolved_circuit.png')