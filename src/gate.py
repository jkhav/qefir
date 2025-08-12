class Gate:
    def __init__(self, name : str, qubits : int, parameter : float = 0.0) -> None:
        self.name = name
        self.qubits = qubits
        self.parameter = parameter
        self.multi_qubit = qubits > 1

class GateSet:
    def __init__(self, gates : list[Gate] = None, preset : str = 'default') -> None:
        if gates is None and preset == 'default':
            raise ValueError('GateSet has to be initialized with list of gates or with preset name')

        if gates is not None:
            self.gates = gates
        elif preset == 'Clifford+T':
            self.gates = [
                Gate(name='h', qubits=1, parameter=0.0),
                Gate(name='s', qubits=1, parameter=0.0),
                Gate(name='cx', qubits=2, parameter=0.0),
                Gate(name='t', qubits=1, parameter=0.0),
                Gate(name='tdg', qubits=1, parameter=0.0),
                Gate(name='sdg', qubits=1, parameter=0.0),
            ]
        elif preset == 'default':
            self.gates = [
                Gate(name='h', qubits=1, parameter=0.0),
                Gate(name='s', qubits=1, parameter=0.0),
                Gate(name='cx', qubits=2, parameter=0.0),
                Gate(name='t', qubits=1, parameter=0.0),
                Gate(name='tdg', qubits=1, parameter=0.0),
                Gate(name='sdg', qubits=1, parameter=0.0),
                Gate(name='cz', qubits=2, parameter=0.0),
            ]

    def add_gate(self, gate : Gate) -> None:
        self.gates.append(gate)

    def get_gates(self) -> list[Gate]:
        return self.gates