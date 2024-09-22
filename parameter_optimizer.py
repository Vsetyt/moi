import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Callable
import pandas as pd
from backtesting import Backtester

class ParameterOptimizer:
    def __init__(self, strategy: Callable, data: pd.DataFrame, initial_params: Dict):
        self.strategy = strategy
        self.data = data
        self.initial_params = initial_params
        self.backtester = Backtester(data)

    def objective_function(self, params: List[float]) -> float:
        param_dict = dict(zip(self.initial_params.keys(), params))
        result = self.backtester.run(self.strategy, param_dict)
        return -result['sharpe_ratio']  # We want to maximize Sharpe ratio, so we minimize its negative

    def optimize(self, method: str = 'Nelder-Mead', max_iterations: int = 100) -> Dict:
        initial_values = list(self.initial_params.values())
        bounds = [(0, None) for _ in initial_values]  # Assuming all parameters are non-negative

        result = minimize(
            self.objective_function,
            initial_values,
            method=method,
            bounds=bounds,
            options={'maxiter': max_iterations}
        )

        optimized_params = dict(zip(self.initial_params.keys(), result.x))
        final_result = self.backtester.run(self.strategy, optimized_params)

        return {
            'optimized_params': optimized_params,
            'sharpe_ratio': -result.fun,
            'total_return': final_result['total_return'],
            'max_drawdown': final_result['max_drawdown'],
            'trade_count': final_result['trade_count']
        }

    def grid_search(self, param_grid: Dict[str, List]) -> Dict:
        best_params = None
        best_sharpe = -np.inf

        for params in self._generate_param_combinations(param_grid):
            result = self.backtester.run(self.strategy, params)
            if result['sharpe_ratio'] > best_sharpe:
                best_sharpe = result['sharpe_ratio']
                best_params = params

        final_result = self.backtester.run(self.strategy, best_params)

        return {
            'optimized_params': best_params,
            'sharpe_ratio': best_sharpe,
            'total_return': final_result['total_return'],
            'max_drawdown': final_result['max_drawdown'],
            'trade_count': final_result['trade_count']
        }

    def _generate_param_combinations(self, param_grid: Dict[str, List]):
        keys = param_grid.keys()
        values = param_grid.values()
        for combination in itertools.product(*values):
            yield dict(zip(keys, combination))

    def genetic_algorithm(self, population_size: int = 50, generations: int = 50, mutation_rate: float = 0.1) -> Dict:
        def create_individual():
            return [np.random.uniform(0, 2) * val for val in self.initial_params.values()]

        population = [create_individual() for _ in range(population_size)]

        for _ in range(generations):
            fitness_scores = [-self.objective_function(ind) for ind in population]
            parents = self._select_parents(population, fitness_scores)
            offspring = self._crossover(parents)
            offspring = self._mutate(offspring, mutation_rate)
            population = offspring

        best_individual = max(population, key=lambda ind: -self.objective_function(ind))
        optimized_params = dict(zip(self.initial_params.keys(), best_individual))
        final_result = self.backtester.run(self.strategy, optimized_params)

        return {
            'optimized_params': optimized_params,
            'sharpe_ratio': -self.objective_function(best_individual),
            'total_return': final_result['total_return'],
            'max_drawdown': final_result['max_drawdown'],
            'trade_count': final_result['trade_count']
        }

    def _select_parents(self, population, fitness_scores):
        return random.choices(population, weights=fitness_scores, k=len(population))

    def _crossover(self, parents):
        offspring = []
        for i in range(0, len(parents), 2):
            parent1, parent2 = parents[i], parents[i+1]
            crossover_point = random.randint(1, len(parent1)-1)
            child1 = parent1[:crossover_point] + parent2[crossover_point:]
            child2 = parent2[:crossover_point] + parent1[crossover_point:]
            offspring.extend([child1, child2])
        return offspring

    def _mutate(self, population, mutation_rate):
        for individual in population:
            if random.random() < mutation_rate:
                index = random.randint(0, len(individual)-1)
                individual[index] *= random.uniform(0.8, 1.2)
        return population