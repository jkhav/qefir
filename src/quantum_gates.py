import numpy as np

# Define all needed gates for two qubit system
I = np.eye(2)

H = np.array([[1/np.sqrt(2), 1/np.sqrt(2)], [1/np.sqrt(2), -1/np.sqrt(2)]], dtype=complex)
H_q0 = np.kron(I, H)
H_q1 = np.kron(H, I)

X = np.array([[0, 1], [1, 0]], dtype=complex)
X_q0 = np.kron(I, X)
X_q1 = np.kron(X, I)

Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Y_q0 = np.kron(I, Y)
Y_q1 = np.kron(Y, I)

T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
T_q0 = np.kron(I, T)
T_q1 = np.kron(T, I)

Tdg = T.conj().T
Tdg_q0 = np.kron(I, Tdg)
Tdg_q1 = np.kron(Tdg, I)

Z = np.array([[1, 0], [0, -1]], dtype=complex)
Z_q0 = np.kron(I, Z)
Z_q1 = np.kron(Z, I)

S = np.array([[1, 0], [0, 1j]], dtype=complex)
S_q0 = np.kron(I, S)
S_q1 = np.kron(S, I)

Sdg = S.conj().T
Sdg_q0 = np.kron(I, Sdg)
Sdg_q1 = np.kron(Sdg, I)

CZ = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, -1]
], dtype=complex)

# CNOT_control_target
CNOT_q1_q0 = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
], dtype=complex)
CNOT_q0_q1 = np.array([
    [1, 0, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0],
    [0, 1, 0, 0]
], dtype=complex)