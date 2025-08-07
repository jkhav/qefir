format long

% define all needed gates for two qubit system
I = eye(2)

H = [1/sqrt(2), 1/sqrt(2); 1/sqrt(2), -1/sqrt(2)]
H_q0 = kron(I, H)
H_q1 = kron(H, I)

X = [0, 1; 1, 0]
X_q0 = kron(I, X)
X_q1 = kron(X, I)

Y = [0, -i; i, 0]
Y_q0 = kron(I, Y)
Y_q1 = kron(Y, I)

T = [1, 0; 0, exp(i*pi/4)]
T_q0 = kron(I, T)
T_q1 = kron(T, I)

Tdg = T'
Tdg_q0 = kron(I, Tdg)
Tdg_q1 = kron(Tdg, I)

Z = [1, 0; 0, -1] 
Z_q0 = kron(I, Z)
Z_q1 = kron(Z, I)

S = [1, 0; 0, i]
S_q0 = kron(I, S)
S_q1 = kron(S, I)

Sdg = S'
Sdg_q0 = kron(I, Sdg)
Sdg_q1 = kron(Sdg, I)

CZ = [1, 0, 0, 0; 0, 1, 0, 0; 0, 0, 1, 0; 0, 0, 0, -1]
%CNOT_control_target
CNOT_q1_q0 = [1, 0, 0, 0; 0, 1, 0, 0; 0, 0, 0, 1; 0, 0, 1, 0]
CNOT_q0_q1 = [1, 0, 0, 0; 0, 0, 0, 1; 0, 0, 1, 0; 0, 1, 0, 0]


% Choose RUS circuit to test

#{
FullUnitary = H_q0 * T_q0 * Z_q1 * H_q0 * CZ * T_q0 * H_q0 * Tdg_q0 * CZ * H_q0 * T_q0 * H_q0 % (I+2jZ)/sqrt(5)
ExpectedMatrix = (I+2*i*Z)/sqrt(5)
#}

#{
FullUnitary = H_q0 * T_q0 * CNOT_q0_q1 * H_q0 * CNOT_q0_q1 * T_q0 * H_q0 % (I + sqrt(2)jX)/sqrt(3)
ExpectedMatrix = (I + sqrt(2)*i*X)/sqrt(3)
#}

#{
FullUnitary = H_q0 * Tdg_q0 * H_q0 * CZ * H_q1 * Tdg_q1 * H_q1 * T_q1 * H_q1 * CZ * H_q0 * Tdg_q0 * H_q0 % (2X + sqrt(2)Y + Z)/sqrt(7)
ExpectedMatrix = (2*X + sqrt(2) * Y + Z) / sqrt(7)
#}

{
FullUnitary = H_q0 * Tdg_q0 * Z_q1 * H_q0 * T_q0 * H_q0 * CZ * S_q0 * H_q0 * Tdg_q0 * H_q0 * T_q0 * H_q0 * S_q0 * CZ * H_q0 * Tdg_q0 * H_q0 * T_q0 * H_q0
ExpectedMatrix = (3*I + 2*i*Z)/sqrt(13)
}

#{
FullUnitary = H_q0 * S_q0 * H_q0 * T_q0 * H_q0 * X_q1 * T_q0 * H_q0 * T_q0 * H_q0 * T_q0 * H_q0 * S_q0 * H_q0 * CZ * H_q0 * T_q0 * H_q0 * T_q0 * X_q1 * H_q0 * T_q0 * H_q0 * S_q0 * H_q0 * CZ * H_q0 * Sdg_q0 * T_q0 * H_q0 * T_q0 * H_q0 * T_q0 * H_q0 * T_q0 * S_q0 * H_q0
ExpectedMatrix = (4*I + i*Z)/sqrt(17)
#}

#{
FullUnitary = H_q0 * T_q0 * X_q1 * H_q0 * T_q0 * H_q0 * CZ * H_q0 * S_q0 * H_q0 * T_q0 * H_q0 * T_q0 * H_q0 * T_q0 * H_q0 * X_q1 * T_q0 * H_q0 * T_q0 * H_q0 * T_q0 * H_q0 * T_q0 * H_q0 * S_q0 * H_q0 * CZ * H_q0 * T_q0 * H_q0 * T_q0 * H_q0
ExpectedMatrix = (5*I + 2*i*Z)/sqrt(29)
#}

% pick the entries of the matrix to reduce it to 2x2 - U00,00 U00,10 U10,10 U10,10
% qubit 0 is in fixed state |0> on input and output, so we need amplitudes
% where e.g. system goes from |00> to |10> -> U00,10 etc.
ReducedMatrix = reshape(FullUnitary([1,3,9,11]), 2,2)

% normalize the reduced matrix -> each column or each row should have norm = 1
% rows/columns of the matrix form an orthonormal basis with respect to the inner product (vectors of length 1)
ReducedMatrix_normalized = ReducedMatrix
for k = 1:columns(ReducedMatrix)
    ReducedMatrix_normalized(:, k) = ReducedMatrix(:, k) / norm(ReducedMatrix(:, k));
end

% are the columns really orthonormal? dot products should be equal to 0
for k = 1:columns(ReducedMatrix)
    for l = 1:columns(ReducedMatrix)
        if k != l
            dot_product = dot(ReducedMatrix_normalized(:, k), ReducedMatrix_normalized(:, l))
        end
    end
end

% is the matrix unitary?
AdjointMatrix = ReducedMatrix_normalized'
IdentityMatrix = AdjointMatrix * ReducedMatrix_normalized

% if they are numerically equal, this results in identity matrix
% if they are equal up to a global phase, the phase will be seen on the diagonal
W = ReducedMatrix_normalized' * ExpectedMatrix

% Checking if two unitary matrices are equal up to a global phase
% https://www.cda.cit.tum.de/files/eda/2022_dac_equivalence_checking_paradigms_in_quantum_circuit_design.pdf (Section 3)
%
% tr(I) = 2^n
% tr(e^j*phi * I) = 2^n * e^j*phi
% |tr(e^j*phi * I)| = |2^n * e^j*phi| = 2^n
% 
% because V = U * e^j*phi
% tr(U' * V) = tr(U' * U * e^j*phi) = tr(e^j*phi)
%
% |tr(U' * V)| = 2^n
% |tr(U' * V)| - 2^n = 0

qubits = 1
delta = abs(trace(W)) - 2^qubits