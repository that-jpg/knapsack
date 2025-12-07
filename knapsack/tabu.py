from copy import deepcopy
from functools import reduce
from time import perf_counter

class TabuList(list):

    def __init__(self, size=3):
        self.size = size
        super(TabuList, self).__init__()

    def append(self, element):
        if len(self) == self.size:
            self.pop(0)
            return super(TabuList, self).append(element)
        return super(TabuList, self).append(element)

    def __contains__(self, move):
        for i in range(len(self)):
            if move == self[i]:
                return True
        return False


class TabuSearch(object):

    def __init__(self, max_time_seconds=300):
        self.iter_counter = 0
        self.iter_better = 0
        self.max_time_seconds = max_time_seconds  # Default: 5 minutes (300 seconds)

    def __call__(self, neighborhood_function, knapsack):
        start_time = perf_counter()
        solutions = neighborhood_function(knapsack)
        sorted_moves = self.sort_moves(solutions)
        [sorted_moves.remove(tabu.reverse()) for tabu in knapsack.tabu_list if tabu.reverse() in sorted_moves]
        best_move = None
        best_solution = knapsack.value
        best_solution_moves = deepcopy(knapsack.moves_made)
        best_solution_items = deepcopy(knapsack.items)
        tabu_ended = False
        time_better = start_time

        while (perf_counter() - start_time) < self.max_time_seconds:
            self.iter_counter += 1
            if not len(sorted_moves) == 0: 
                candidate_move = sorted_moves.pop(0) 
                actual_solution = knapsack.value + candidate_move.movement_avaliation
                # Only execute if movement is valid
                if knapsack.execute_movement(candidate_move):
                    knapsack.tabu_list.append(candidate_move.reverse())
                else:
                    # Movement failed, skip it and continue
                    continue
                if actual_solution > best_solution:
                    elapsed_time = perf_counter() - start_time
                    # print("Current iter %d (%.2f s), actual solution %d, better solution found at %.2f s with %d" % (self.iter_counter, elapsed_time, actual_solution, time_better - start_time, best_solution))
                    best_solution = actual_solution
                    best_solution_moves = deepcopy(knapsack.moves_made)
                    best_solution_items = deepcopy(knapsack.items)
                    self.iter_better = self.iter_counter
                    time_better = perf_counter()
            else:
                best_tabu = reduce(lambda x, y: x if x.movement_avaliation > y.movement_avaliation else y, knapsack.tabu_list)
                if best_tabu.movement_avaliation > 0: # se ele apresentar uma melhora real na solucao atual
                    actual_solution = knapsack.value + best_tabu.movement_avaliation
                    if actual_solution > best_solution:
                        elapsed_time = perf_counter() - start_time
                        best_solution = actual_solution
                        best_solution_moves = deepcopy(knapsack.moves_made)
                        best_solution_items = deepcopy(knapsack.items)
                        self.iter_better = self.iter_counter
                        time_better = perf_counter()
                    # Only execute if movement is valid
                    if not knapsack.execute_movement(best_tabu):
                        # Movement failed, skip it
                        pass
            solutions = neighborhood_function(knapsack)
            sorted_moves = self.sort_moves(solutions)
            [sorted_moves.remove(tabu.reverse()) for tabu in knapsack.tabu_list if tabu.reverse() in sorted_moves]
            
        elapsed_time = perf_counter() - start_time
        knapsack.value = best_solution
        knapsack.items = best_solution_items
        knapsack.moves_made = best_solution_moves

        print('Script ran with tabu search for %.2f seconds (%d iterations) and a tabu list with size %d.' % (elapsed_time, self.iter_counter, knapsack.tabu_list.size))
        print('Ended by time limit (%.2f seconds).' % self.max_time_seconds)
        return False

    def sort_moves(self, moves):
        return sorted(moves, key=lambda x: x.movement_avaliation, reverse=True)
