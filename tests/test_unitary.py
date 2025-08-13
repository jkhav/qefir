import subprocess
import numpy as np
import sys

sys.path.append('../')
import src.quantum_gates as qg
sys.path.append('tests/')

def print_matrix(matrix):
    # https://stackoverflow.com/questions/17870612/printing-a-two-dimensional-array-in-python
    rows = matrix.shape[0]
    cols = matrix.shape[1]
    for i in range(rows):
        print('\t', end = '')
        for j in range(cols):
            value = matrix[i, j]
            if np.iscomplexobj(value):
                print(f"{value.real:8.3f}{value.imag:+.3f}j", end=' ')
            else:
                print(f"{float(value):8.3f}", end=' ')
        print()
    print()

def parse_ddsim_output(res_str):
    """
    Example:
    [0.25-0.25j,0.25+0.25j,0.146447-0.853553j,0+0j,]
    [0.25+0.25j,0.25-0.25j,0+0j,-0.146447+0.853553j,]
    [0.853553-0.146447j,0+0j,-0.25+0.25j,-0.25-0.25j,]
    [0+0j,-0.853553+0.146447j,-0.25-0.25j,-0.25+0.25j,]
    """
    matrix = []
    for line in res_str.split('\n'):
        if line.startswith('['):
            elements = [x.strip() for x in line.strip('[]').split(',') if x.strip()]
            row = []
            for elem in elements:
                try:
                    row.append(complex(elem))
                except ValueError:
                    row.append(0j)
            matrix.append(row)
    return matrix

def trace(matrix):
    return sum(matrix[i][i] for i in range(len(matrix)))

def adjoint(matrix):
    return np.conj(np.transpose(matrix))

def reduce_matrix(matrix):
    can_normalize = True
    q1_matrix = [[matrix[0][0], matrix[0][2]], [matrix[2][0], matrix[2][2]]]
    for i in range(len(q1_matrix)):
        norm = np.linalg.norm(q1_matrix[i])
        if norm == 0:
            can_normalize = False
            return q1_matrix, can_normalize
        q1_matrix[i] /= norm
    return q1_matrix, can_normalize

def test(filename):
    res = subprocess.run(['../src/ddsim', '--simulate_unitary', filename, '--pu'], capture_output=True)
    res_str = res.stdout.decode('utf-8')
    matrix = parse_ddsim_output(res_str)

    print(f"- Matrix output:")
    print_matrix(np.matrix(matrix))
    reduced_matrix, normalized = reduce_matrix(matrix)
    print(f"- Reduced, normalized Matrix:")
    print_matrix(np.matrix(reduced_matrix))

    # check if the matrix is unitary
    product = reduced_matrix @ adjoint(reduced_matrix)
    print(f"- Result * Adjoint(Result) should yield I:")
    print_matrix(product)

    expected_gate = (2 * qg.X + np.sqrt(2) * qg.Y + qg.Z) / np.sqrt(7)
    #expected_gate = (qg.I + np.sqrt(2) * 1j * qg.X) / np.sqrt(3)
    #expected_gate = (1 * qg.I + 2j * qg.Z) / np.sqrt(5)
    #expected_gate = (3 * qg.I + 2j * qg.Z) / np.sqrt(13)
    #expected_gate = (4 * qg.I + 1j * qg.Z) / np.sqrt(17)
    #expected_gate = (5 * qg.I + 2j * qg.Z) / np.sqrt(29)

    product = expected_gate @ adjoint(reduced_matrix)
    print(f"- Product of Expected @ Adjoint(Reduced):")
    print_matrix(product)
    trace = np.trace(product)
    print(f"\t- Trace of the product:\n\t\t{trace}")
    n = 1
    trace_fitness = np.abs(trace) - 2**n
    print(f"\t- Absolute value of trace should be around 2^n:\n\t\t{np.abs(trace)}")
    print(f"\t- Abs(trace) - 2^n should be 0:\n\t\t{np.abs(trace) - 2**n}")
    print()
    print(f"- Distance of the two matrices:\n\t{np.linalg.norm((expected_gate - reduced_matrix), 'fro')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file = sys.argv[1]
        test(file)

    else:
        file = '../src/final_circuit.qasm'
        test(file)