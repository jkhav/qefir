class Gate:
    def __init__(self, name : str, qubits : int, parameter : float = 0.0) -> None:
        self.name = name
        self.qubits = qubits
        self.parameter = parameter
        self.multi_qubit = qubits > 1