import numpy as np


class ExpressionParser:
    def __init__(self, expression: str):
        self.expression = expression
        
    def parse(self):
        # parse expression into np.array
        # expression to statevector mapping
        # (5I + 2iZ)/sqrt(29) should become
        # ---> np.array([1, 0]) * ((5 + 2j)/np.sqrt(29)) + 0 * np.array([0, 1])
        # ---> np.array([1, 0]) * 0 + np.array([0, 1]) * ((5 - 2j)/np.sqrt(29))
        pass
