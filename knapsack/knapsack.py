from time import perf_counter
from copy import deepcopy
from functools import reduce


class Item(object):

    def __init__(self, name, value, weight, volume):
        self.name = name
        self.value = value
        self.weight = weight
        self.volume = volume

    def __repr__(self):
        return "<%s>" % self.name        

    def ratio(self):
        return float(self.value) / (self.weight + self.volume)

    def __eq__(self, item):
        return self.name == item.name and self.value == item.value and self.weight == item.weight and self.volume == item.volume
        

class Knapsack(object):

    def __init__(self, weight, volume, all_items, **kwargs):
        self.weight = self.initial_weight = weight
        self.volume = self.initial_volume = volume
        self.value = 0
        self.all_items = all_items
        self.initial_value = 0
        self.items = []
        self.movement_counter = 0
        self.moves_made = []
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])

    def optimize(self, initial_solution_function, heuristic_function, neighborhood_function):
        start = perf_counter()
        initial_solution_function(self)
        self.initial_solution = deepcopy(self.items)
        self.initial_value = self.value
        heuristic_function(neighborhood_function, self)
        end = perf_counter()
        
        # Validate final solution
        total_weight = sum(item.weight for item in self.items)
        total_volume = sum(item.volume for item in self.items)
        total_value = sum(item.value for item in self.items)
        used_weight = self.initial_weight - self.weight
        used_volume = self.initial_volume - self.volume
        
        # Check if tracked value matches sum of item values
        if self.value != total_value:
            print('ERROR: Value mismatch detected!')
            print(f'  Tracked value: {self.value}, Sum of item values: {total_value}, Difference: {self.value - total_value}')
            print(f'  This suggests items may have been double-counted or value tracking is incorrect!')
        
        # Check for duplicate items
        item_names = [item.name for item in self.items]
        if len(item_names) != len(set(item_names)):
            print('ERROR: Duplicate items found in solution!')
            from collections import Counter
            duplicates = [item for item, count in Counter(item_names).items() if count > 1]
            print(f'  Duplicate items: {duplicates}')
        
        if total_weight != used_weight or total_volume != used_volume:
            print('ERROR: Solution validation failed!')
            print(f'  Total item weights: {total_weight}, Used weight: {used_weight}, Difference: {total_weight - used_weight}')
            print(f'  Total item volumes: {total_volume}, Used volume: {used_volume}, Difference: {total_volume - used_volume}')
            print(f'  Initial weight: {self.initial_weight}, Initial volume: {self.initial_volume}')
            print(f'  Weight left: {self.weight}, Volume left: {self.volume}')
        
        if self.weight < 0 or self.volume < 0:
            print('ERROR: Negative remaining capacity!')
            print(f'  Weight left: {self.weight}, Volume left: {self.volume}')
            print(f'  This means constraints are violated!')
        
        # Verify all items are unique
        seen_items = set()
        for item in self.items:
            item_key = (item.name, item.value, item.weight, item.volume)
            if item_key in seen_items:
                print(f'ERROR: Duplicate item found: {item}')
            seen_items.add(item_key)
        
        # Print detailed solution info for debugging
        print(f'\nSolution validation:')
        print(f'  Number of items: {len(self.items)}')
        print(f'  Total value (tracked): {self.value}')
        print(f'  Total value (calculated): {total_value}')
        print(f'  Total weight: {total_weight}, Used weight: {used_weight}')
        print(f'  Total volume: {total_volume}, Used volume: {used_volume}')
        print(f'  Weight left: {self.weight}, Volume left: {self.volume}')
        
        print('Best solution found with %d move(s).' % len(self.moves_made))
        print('Initial solution was: %s' % self.initial_solution)
        print('Movements made: ')
        for move in self.moves_made:
            print('-'*3 + " %s " % str(move))
        print('Initial value: %d' % self.initial_value)
        print('Final value: %d' % self.value)
        print('Total improvement: %d' % (self.value - self.initial_value))
        print('Weight left: %d' % self.weight)
        print('Volume left: %d' % self.volume)
        print('Number of items in solution: %s' % len(self.items))
        print('Ran in %f milliseconds.' % ((end-start)*1000))

    def execute_movement(self, movement):
        """
        Execute a movement by removing items first, then adding items.
        If any step fails, the movement is rolled back to maintain consistency.
        """
        # First, validate the entire movement before executing anything
        # Check if all remove_items are in the knapsack
        for item in movement.remove_items:
            if item not in self:
                return False
        
        # Simulate the movement to check if all add_items can fit after removals
        # Calculate what items would remain after removals
        temp_items = [item for item in self.items if item not in movement.remove_items]
        
        # Calculate available capacity after removals
        # Start with initial capacity
        temp_weight = self.initial_weight
        temp_volume = self.initial_volume
        # Subtract capacity used by remaining items
        for item in temp_items:
            temp_weight -= item.weight
            temp_volume -= item.volume
        
        # Check for duplicate items in add_items
        add_items_set = set()
        for item in movement.add_items:
            # Use a tuple for hashing (name, value, weight, volume)
            item_key = (item.name, item.value, item.weight, item.volume)
            if item_key in add_items_set:
                return False  # Duplicate item in add_items
            add_items_set.add(item_key)
        
        # Check if all items to be added can fit and are not already in remaining items
        for item in movement.add_items:
            # Check if item is already in remaining items (shouldn't be added twice)
            if item in temp_items:
                return False
            # Check if item fits in available capacity
            if item.weight > temp_weight or item.volume > temp_volume:
                return False
            temp_weight -= item.weight
            temp_volume -= item.volume
        
        # If validation passes, execute the movement
        # Remove items first
        for item in movement.remove_items:
            self.remove_item(item)
        
        # Add items
        for item in movement.add_items:
            # Double-check before adding (safety check)
            if not self.can_add_item(item):
                # This should not happen if validation above was correct
                # But if it does, we need to rollback
                for removed_item in movement.remove_items:
                    if removed_item not in self.items:
                        # Use add_item which will check constraints
                        if not self.add_item(removed_item):
                            print(f'ERROR: Failed to rollback removed item {removed_item}')
                return False
            # Check if item is already in knapsack (shouldn't happen but double-check)
            if item in self.items:
                print(f'WARNING: Trying to add item {item} that is already in knapsack!')
                # Rollback: restore removed items
                for removed_item in movement.remove_items:
                    if removed_item not in self.items:
                        # Manually restore the item (bypassing can_add_item check since we know it was there before)
                        self.items.append(removed_item)
                        self.weight -= removed_item.weight
                        self.volume -= removed_item.volume
                        self.value += removed_item.value
                        if removed_item not in self.all_items:
                            self.all_items.append(removed_item)
                return False
            self.add_item(item)
        
        return True

    def add_item(self, item):
        if self.can_add_item(item):
            # Check if item is already in items (shouldn't happen but double-check)
            if item in self.items:
                print(f'ERROR: Attempting to add item {item} that is already in items list!')
                return False
            self.items.append(item)
            self.weight -= item.weight
            self.volume -= item.volume
            self.value += item.value
            # Only remove from all_items if it's there
            if item in self.all_items:
                self.all_items.remove(item)
            return True
        return False

    def evaluate_swap(self, item, another_item):
        return self.can_swap(item, another_item)

    def remove_item(self, item):
        # Find the item in the list (using __eq__ comparison)
        item_to_remove = None
        for i in self.items:
            if i == item:  # Uses __eq__ method
                item_to_remove = i
                break
        
        if item_to_remove is not None:
            # Use the actual item from the list to ensure we have the right weight/volume
            actual_weight = item_to_remove.weight
            actual_volume = item_to_remove.volume
            actual_value = item_to_remove.value
            
            self.weight += actual_weight
            self.volume += actual_volume
            self.value -= actual_value
            self.items.remove(item_to_remove)
            # Only add back to all_items if it's not already there
            if item_to_remove not in self.all_items:
                self.all_items.append(item_to_remove)
            return True
        return False

    def can_swap(self, inside_item, another_item):
        if not inside_item in self or another_item in self:
            return False
        new_weight = self.weight + inside_item.weight
        new_volume = self.volume + inside_item.volume
        if (another_item.weight <= new_weight and another_item.volume <= new_volume):
            return self.value < (self.value - inside_item.value + another_item.value)
        return False

    def swap(self, item, another_item):
        if self.can_swap(item, another_item):
            self.remove_item(item)
            self.add_item(another_item)
            return True
        return False

    def __contains__(self, item):
        return any(map(lambda x: x == item, self.items))

    def can_add_item(self, item):
        if (self.weight >= item.weight and self.volume >= item.volume and not item in self.items):        
            return True
        return False

    def __repr__(self):
        return "<Knapsack (%d) %s>" % (len(self.items), repr(self.items))

    def sorted_items(self, items, key=Item.ratio):
        return sorted(items, key=key, reverse=True)

    def solution_neighborhood(self, f):
        return f(self)


class Movement(object):

    def __init__(self, add_items=[], remove_items=[]):
        self.add_items = add_items
        self.remove_items = remove_items

    @property
    def movement_avaliation(self):
        remove_value = add_value = 0
        if not len(self.remove_items) == 0:
            remove_value = reduce(lambda x, y: x + y, [item.value for item in self.remove_items])
        if not len(self.add_items) == 0:
            add_value = reduce(lambda x, y: x + y, [item.value for item in self.add_items])
        return add_value - remove_value

    def reverse(self):
        return Movement(add_items=self.remove_items, remove_items=self.add_items)

    def __eq__(self, another_move):
        if not isinstance(another_move, Movement):
            return False
        return self.add_items == another_move.add_items and self.remove_items == another_move.remove_items

    def __repr__(self):        
        return "<Remove %s | Add %s | Improve %d>" % (self.remove_items, self.add_items, self.movement_avaliation)