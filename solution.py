import pandas as pd
import numpy as np

df01 = pd.read_excel('matriz_cenarios.xlsx', sheet_name='C_01')

df01 = df01.set_index('Unnamed: 0')

df01 = df01.replace('-', 0)

matriz01 = df01.to_numpy()

from hygese import AlgorithmParameters, Solver

data = dict()
data['distance_matrix'] = matriz01
data['num_vehicles'] = 1
data['depot'] = 0
data['demands'] = [1]*58
data['demands'][0] = 0
data['vehicle_capacity'] = 150  # different from OR-Tools: homogeneous capacity
data['service_times'] = np.zeros(len(data['demands']))

# Solver initialization
ap = AlgorithmParameters(timeLimit=3.2)  # seconds
hgs_solver = Solver(parameters=ap, verbose=True)

# Solve
result = hgs_solver.solve_cvrp(data)
print(result.cost)
print(result.routes)