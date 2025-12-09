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
               
        # Verify all items are unique and remove duplicates if found
        seen_items = {}
        unique_items = []
        for item in self.items:
            item_key = (item.name, item.value, item.weight, item.volume)
            if item_key in seen_items:
                print(f'ERROR: Duplicate item found: {item}, removing duplicate')
                continue  # Skip duplicate
            seen_items[item_key] = item
            unique_items.append(item)
        
        # If duplicates were found, update items list and recalculate
        if len(unique_items) != len(self.items):
            print(f'WARNING: Found {len(self.items) - len(unique_items)} duplicate items, removing them')
            self.items = unique_items
            # Recalculate everything after removing duplicates
            total_weight = sum(item.weight for item in self.items)
            total_volume = sum(item.volume for item in self.items)
            total_value = sum(item.value for item in self.items)
        
        # Always recalculate from items to ensure consistency (fixes any tracking errors)
        self.value = total_value
        self.weight = self.initial_weight - total_weight
        self.volume = self.initial_volume - total_volume
        
        # Verify value consistency (should always match now, but check for debugging)
        if total_value != self.value:
            print(f'ERROR: Value mismatch after recalculation! Calculated: {total_value}, Tracked: {self.value}')
        
        # Verify weight consistency
        if total_weight != used_weight:
            print(f'WARNING: Weight was inconsistent! Calculated: {total_weight}, Was tracked as: {used_weight}')
        
        # Verify volume consistency
        if total_volume != used_volume:
            print(f'WARNING: Volume was inconsistent! Calculated: {total_volume}, Was tracked as: {used_volume}')
        
        # Verify constraints are not violated
        if total_weight > self.initial_weight:
            print(f'ERROR: Weight constraint violated! {total_weight} > {self.initial_weight}')
            self.value = 0  # Invalid solution
        if total_volume > self.initial_volume:
            print(f'ERROR: Volume constraint violated! {total_volume} > {self.initial_volume}')
            self.value = 0  # Invalid solution
        
        # Final validation: ensure all items in knapsack are from all_items (or were added properly)
        # and that no item appears in both items and all_items
        # Clean up all_items first
        self._cleanup_all_items()
        
        items_in_knapsack = set((item.name, item.value, item.weight, item.volume) for item in self.items)
        items_available = set((item.name, item.value, item.weight, item.volume) for item in self.all_items)
        overlap = items_in_knapsack & items_available
        if overlap:
            print(f'WARNING: {len(overlap)} items are both in knapsack and in all_items (should not happen)')
            # Remove overlapping items from all_items (keep them in knapsack)
            items_to_remove_from_all = []
            for item in self.all_items:
                item_key = (item.name, item.value, item.weight, item.volume)
                if item_key in overlap:
                    items_to_remove_from_all.append(item)
            for item in items_to_remove_from_all:
                self.all_items.remove(item)
        
        # Print detailed solution info for debugging
        print('Final value: %d (items: %d, weight: %d/%d, volume: %d/%d)' % 
              (self.value, len(self.items), total_weight, self.initial_weight, total_volume, self.initial_volume))
 
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
        # Also check that items to be added are not already in the current knapsack
        for item in movement.add_items:
            # Check if item is already in remaining items (shouldn't be added twice)
            if item in temp_items:
                return False
            # Check if an item with the same properties is already in the current knapsack
            # (might be a different object with same properties)
            if item in self.items:
                return False
            # Check if item fits in available capacity
            if item.weight > temp_weight or item.volume > temp_volume:
                return False
            temp_weight -= item.weight
            temp_volume -= item.volume
        
        # Clean up all_items before executing movement to ensure consistency
        self._cleanup_all_items()
        
        # If validation passes, execute the movement
        # Remove items first
        for item in movement.remove_items:
            self.remove_item(item)
        
        # Add items
        added_items = []  # Track successfully added items for rollback
        for item in movement.add_items:
            # Double-check before adding (safety check)
            if not self.can_add_item(item):
                # Rollback: remove any items that were successfully added
                for added_item in added_items:
                    if added_item in self.items:
                        self.remove_item(added_item)
                # Rollback: restore removed items
                for removed_item in movement.remove_items:
                    if removed_item not in self.items:
                        # Use add_item which will check constraints
                        if not self.add_item(removed_item):
                            print(f'ERROR: Failed to rollback removed item {removed_item}')
                return False
            # Check if item is already in knapsack (shouldn't happen but double-check)
            if item in self.items:
                print(f'WARNING: Trying to add item {item} that is already in knapsack!')
                # Rollback: remove any items that were successfully added
                for added_item in added_items:
                    if added_item in self.items:
                        self.remove_item(added_item)
                # Rollback: restore removed items using add_item to ensure proper tracking
                for removed_item in movement.remove_items:
                    if removed_item not in self.items:
                        # Use add_item which will properly track weight, volume, and value
                        # Note: add_item might fail if constraints are violated, but in rollback
                        # we know the item was there before, so we can bypass the check
                        # However, we should still use add_item to maintain consistency
                        if not self.add_item(removed_item):
                            # If add_item fails (shouldn't happen in rollback), manually restore
                            # but ensure we're using the actual item object, not a reference
                            actual_item = removed_item
                            # Find the actual item in all_items if it exists there
                            for i in self.all_items:
                                if i == removed_item:
                                    actual_item = i
                                    break
                            self.items.append(actual_item)
                            self.weight -= actual_item.weight
                            self.volume -= actual_item.volume
                            self.value += actual_item.value
                            # Remove from all_items if it's there
                            if actual_item in self.all_items:
                                self.all_items.remove(actual_item)
                return False
            if self.add_item(item):
                added_items.append(item)
            else:
                # add_item failed, rollback
                for added_item in added_items:
                    if added_item in self.items:
                        self.remove_item(added_item)
                for removed_item in movement.remove_items:
                    if removed_item not in self.items:
                        if not self.add_item(removed_item):
                            print(f'ERROR: Failed to rollback removed item {removed_item}')
                return False
        
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
            # Remove from all_items - need to find by identity or equality
            # Find ALL items in all_items that are equal to this item (might be multiple objects with same properties)
            items_to_remove = []
            for i in self.all_items:
                if i == item:  # Uses __eq__ method
                    items_to_remove.append(i)
            for item_to_remove in items_to_remove:
                self.all_items.remove(item_to_remove)
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
            # Add back to all_items - check if an equal item is already there
            # (might be a different object with same properties)
            item_already_there = None
            for i in self.all_items:
                if i == item_to_remove:  # Uses __eq__ method
                    item_already_there = i
                    break
            if item_already_there is None:
                self.all_items.append(item_to_remove)
            # If an equal item is already there, we don't need to add it again
            # but we should ensure we're not keeping duplicate references
            return True
        return False

    def can_swap(self, inside_item, another_item):
        # inside_item must be in knapsack, another_item must not be in knapsack
        if inside_item not in self or another_item in self:
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

    def _cleanup_all_items(self):
        """Remove any items from all_items that are equal to items already in the knapsack."""
        items_to_remove = []
        for item in self.all_items:
            if item in self.items:  # Uses __eq__ method
                items_to_remove.append(item)
        for item in items_to_remove:
            self.all_items.remove(item)
    
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