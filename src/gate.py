class Gate:
    def __init__(self, name : str, qubits : int, parameter : float = 0.0) -> None:
        self.name = name
        self.qubits = qubits
        self.parameter = parameter
        self.multi_qubit = qubits > 1

    def __eq__(self, other : "Gate") -> bool:
        return (self.name == other.name) and (self.qubits == other.qubits) and (self.parameter == other.parameter)

    def __ne__(self, other : "Gate") -> bool:
        return not (self == other)

class GateSet:
    def __init__(self, gates : list[Gate] = None, preset : str = None) -> None:
        if gates is None and preset is None:
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

    def remove_gate(self, gate : Gate = None, name : str = None) -> None:
        if gate is None and name is None:
            raise ValueError('Failed removing a gate, did not specify any parameter')
        
        if name is not None:
            self.gates = [g for g in self.gates if g.name != name]
        elif gate is not None:
            self.gates = [g for g in self.gates if g != gate]