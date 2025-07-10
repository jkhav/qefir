class Gate:
    def __init__(self, name='', qubits=1, parameter=0.0):
        self.name = name
        self.qubits = qubits
        self.parameter = parameter
        self.multi_qubit = qubits > 1
        self.multi_qubit_idx = 0
