import datetime

class Logger:
    def __init__(self, filename='logs/evolution'):
        self.filename = filename + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.log'
        self.file = open(self.filename, 'w')
        self.start_time = datetime.datetime.now()
        
        self.fitness_calls = 0
        self.fitness_time = 0.0
        
        self.mutations = 0
        self.s_to_s_mutation_calls = 0
        self.m_to_m_mutation_calls = 0
        self.m_to_s_mutation_calls = 0
        self.s_to_m_mutation_calls = 0
        self.mutations_time = 0.0
        
        self.useless_mutations = 0
    
    def log(self, type='MISC', message='default message'):
        """
        Log a message to the log file with runtime since logger creation
        """
        runtime = datetime.datetime.now() - self.start_time
        self.file.write(f"[{type}] (runtime: {runtime}) {message}\n")
    
    def close(self):
        self.file.close()
        
    def log_fitness_call(self, time_taken):
        """
        Log a fitness function call with time taken
        """
        self.fitness_calls += 1
        self.fitness_time += time_taken
        
    def log_mutation(self, time_taken):
        """
        Log a mutation with its type
        """
        self.mutations += 1
        self.mutations_time += time_taken
        
    def log_s_to_s_mutation(self):
        """
        Log a mutation from S to S
        """
        self.s_to_s_mutation_calls += 1
        
    def log_m_to_m_mutation(self):
        """
        Log a mutation from M to M
        """
        self.m_to_m_mutation_calls += 1
        
    def log_m_to_s_mutation(self):
        """
        Log a mutation from M to S
        """
        self.m_to_s_mutation_calls += 1
        
    def log_s_to_m_mutation(self):
        """
        Log a mutation from S to M
        """
        self.s_to_m_mutation_calls += 1
        
    def log_useless_mutation(self):
        self.useless_mutations += 1
    
    def print_stats(self):
        """
        Print statistics about the evolution process
        """
        self.file.write("\n--- Evolution Statistics ---\n")
        self.file.write(f"Total fitness calls: {self.fitness_calls}\n")
        self.file.write(f"Total fitness time: {self.fitness_time:.4f} seconds\n")
        
        self.file.write(f"Total mutations: {self.mutations}\n")
        self.file.write(f"Total mutation time: {self.mutations_time:.4f} seconds\n")
        self.file.write(f"S to S mutations: {self.s_to_s_mutation_calls}\n")
        self.file.write(f"M to S mutations: {self.m_to_s_mutation_calls}\n")
        self.file.write(f"S to M mutations: {self.s_to_m_mutation_calls}\n")
        self.file.write(f"Useless mutations: {self.useless_mutations}\n")
        self.file.write(f"\n")
        
    def print_final_circuit(self, individual):
        """
        Print the final circuit to the log file
        """
        self.file.write("\n--- Final Circuit ---\n")
        self.file.write(individual.to_qasm())
        self.file.write(f"\n")
