import sklearn.datasets
import numpy as np
import random
from sklearn.neural_network import MLPClassifier

data = sklearn.datasets.load_digits()
X = data["data"]
y = data["target"]

from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold

paramgrid = {"kernel": ["rbf"],
             "C"     : np.logspace(-9, 9, num=25, base=10),
             "gamma" : np.logspace(-9, 9, num=25, base=10)}

random.seed(1)

est = MLPClassifier(solver='lbfgs',
                        alpha=1e-5,
                        hidden_layer_sizes=(2),
                        random_state=1)

from evolutionary_search import EvolutionaryAlgorithmSearchCV
cv = EvolutionaryAlgorithmSearchCV(estimator=SVC(),
                                   params=paramgrid,
                                   scoring="accuracy",
                                   cv=StratifiedKFold(n_splits=4),
                                   verbose=1,
                                   population_size=50,
                                   gene_mutation_prob=0.10,
                                   gene_crossover_prob=0.5,
                                   tournament_size=3,
                                   generations_number=5,
                                   n_jobs=1)
cv.fit(X, y)

from evolutionary_search import maximize

def func(x, y, m=1., z=False):
    return m * (np.exp(-(x**2 + y**2)) + float(z))

param_grid = {'x': [-1., 0., 1.], 'y': [-1., 0., 1.], 'z': [True, False]}
args = {'m': 1.}
best_params, best_score, score_results, hist, logbook = maximize(func, param_grid, args, verbose=False)

print(best_params)
print(best_score)
print(score_results)
#TODO: test this program with Neural Network Model