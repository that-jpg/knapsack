from .knapsack import Movement, Knapsack
from random import choice, shuffle, random, sample, randint
from copy import deepcopy

def all_neighborhood(knapsack):
    neighborhood = []
    improving_solutions = []
    shuffle(knapsack.all_items)
    for item in knapsack.all_items:
        i = 0
        actual_value = knapsack.value
        shuffle(knapsack.items)

        # Try to create movements that remove items to make room
        to_remove = []
        volume_to_lose = item.volume
        weight_to_lose = item.weight
        # Only try if the item doesn't fit
        if not knapsack.can_add_item(item):
            # Try to find items to remove to make room
            available_items = [it for it in knapsack.items if it not in to_remove]
            while (volume_to_lose > 0 or weight_to_lose > 0) and len(available_items) > 0:
                solution_item = choice(available_items)
                to_remove.append(solution_item)
                weight_to_lose -= solution_item.weight
                volume_to_lose -= solution_item.volume
                available_items.remove(solution_item)
                i += 1
                # Only add movement if we've freed enough space
                if weight_to_lose <= 0 and volume_to_lose <= 0:
                    movement = Movement(add_items=[item,], remove_items=to_remove[:])
                    neighborhood.append(movement)

        # Try simple add (if item fits directly)
        if knapsack.can_add_item(item):
            movement = Movement(add_items=[item,])
            neighborhood.append(movement)
        
        # Try swaps
        for solution_item in knapsack.items:
            if knapsack.can_swap(solution_item, item):
                new_value = knapsack.evaluate_swap(solution_item, item)
                movement = Movement(add_items=[item,], remove_items=[solution_item,])
                neighborhood.append(movement)
    return neighborhood

def first_improving_neighborhood(knapsack):
    neighborhood = []
    improving_solution = None
    for item in knapsack.sorted_items(knapsack.all_items):
        actual_value = knapsack.value
        for solution_item in knapsack.sorted_items(knapsack.items):
            if knapsack.can_swap(solution_item, item):
                new_value = knapsack.evaluate_swap(solution_item, item)
                movement = Movement(add_items=[item,], remove_items=[solution_item,])
                if new_value > knapsack.value:
                    improving_solution = movement
                    neighborhood.append(movement)
                    return neighborhood
                neighborhood.append(movement)
            else:
                pass
    return neighborhood


def genetic_algorithm_neighborhood(knapsack, population_size=20, generations=5, mutation_rate=0.1, crossover_rate=0.7):
    """
    A neighborhood function that uses genetic algorithm principles to generate candidate movements.
    
    Parameters:
    - population_size: Number of movements in each generation
    - generations: Number of generations to evolve
    - mutation_rate: Probability of mutating a movement
    - crossover_rate: Probability of performing crossover between two movements
    
    Returns:
    - A list of Movement objects representing the evolved neighborhood
    """
    # Initialize population with random movements
    population = _initialize_population(knapsack, population_size)
    
    # Evolve for specified number of generations
    for generation in range(generations):
        # Evaluate fitness (movement_avaliation)
        population.sort(key=lambda m: m.movement_avaliation, reverse=True)
        
        # Create new generation through selection, crossover, and mutation
        new_population = []
        
        # Elitism: Keep top 20% of the population
        elite_size = max(1, int(population_size * 0.2))
        new_population.extend(population[:elite_size])
        
        # Generate remaining individuals
        attempts = 0
        max_attempts = population_size * 10
        while len(new_population) < population_size and attempts < max_attempts:
            attempts += 1
            # Selection: Tournament selection
            parent1 = _tournament_selection(population, tournament_size=3)
            parent2 = _tournament_selection(population, tournament_size=3)
            
            # Crossover
            if random() < crossover_rate:
                child = _crossover(parent1, parent2, knapsack)
            else:
                child = deepcopy(parent1)
            
            # Mutation
            if random() < mutation_rate:
                child = _mutate(child, knapsack)
            
            # Only add valid movements
            if _is_valid_movement(child, knapsack):
                new_population.append(child)
        
        # If we couldn't generate enough valid movements, fill with copies of best ones
        while len(new_population) < population_size and len(population) > 0:
            new_population.append(deepcopy(choice(population[:elite_size])))
        
        population = new_population
    
    # Return final population sorted by fitness
    population.sort(key=lambda m: m.movement_avaliation, reverse=True)
    return population


def _initialize_population(knapsack, size):
    """Initialize population with random movements."""
    population = []
    available_items = deepcopy(knapsack.all_items)
    current_items = deepcopy(knapsack.items)
    shuffle(available_items)
    shuffle(current_items)
    
    attempts = 0
    max_attempts = size * 10
    
    while len(population) < size and attempts < max_attempts:
        attempts += 1
        
        # Randomly decide to add, remove, or swap
        action = random()
        
        if action < 0.4 and len(available_items) > 0:  # Add item
            item = choice(available_items)
            if knapsack.can_add_item(item):
                movement = Movement(add_items=[item])
                population.append(movement)
        
        elif action < 0.7 and len(current_items) > 0:  # Remove item
            item = choice(current_items)
            if item in knapsack:
                movement = Movement(remove_items=[item])
                population.append(movement)
        
        elif len(available_items) > 0 and len(current_items) > 0:  # Swap items
            add_item = choice(available_items)
            remove_item = choice(current_items)
            if remove_item in knapsack and knapsack.can_swap(remove_item, add_item):
                movement = Movement(add_items=[add_item], remove_items=[remove_item])
                population.append(movement)
    
    # If we don't have enough, fill with empty movements (no-op)
    while len(population) < size:
        population.append(Movement())
    
    return population


def _tournament_selection(population, tournament_size=3):
    """Select a movement using tournament selection."""
    tournament = sample(population, min(tournament_size, len(population)))
    return max(tournament, key=lambda m: m.movement_avaliation)


def _crossover(parent1, parent2, knapsack):
    """Create a child movement by combining two parent movements."""
    # Combine add_items from both parents (with some randomness)
    add_items = []
    if random() < 0.5:
        add_items.extend(deepcopy(parent1.add_items))
    if random() < 0.5:
        add_items.extend(deepcopy(parent2.add_items))
    
    # Combine remove_items from both parents (with some randomness)
    remove_items = []
    if random() < 0.5:
        remove_items.extend(deepcopy(parent1.remove_items))
    if random() < 0.5:
        remove_items.extend(deepcopy(parent2.remove_items))
    
    # Remove duplicates (using list comprehension since Item objects may not be hashable)
    seen_add = []
    for item in add_items:
        if item not in seen_add:
            seen_add.append(item)
    add_items = seen_add
    
    seen_remove = []
    for item in remove_items:
        if item not in seen_remove:
            seen_remove.append(item)
    remove_items = seen_remove
    
    # Remove items that are both added and removed (conflicting)
    add_items = [item for item in add_items if item not in remove_items]
    
    return Movement(add_items=add_items, remove_items=remove_items)


def _mutate(movement, knapsack):
    """Mutate a movement by randomly modifying it."""
    mutated = deepcopy(movement)
    
    # Randomly add or remove items from the movement
    if random() < 0.5 and len(knapsack.all_items) > 0:
        # Add a random item
        item = choice(knapsack.all_items)
        if item not in mutated.add_items:
            mutated.add_items.append(item)
            # Remove conflicting items from remove_items
            mutated.remove_items = [r for r in mutated.remove_items if r != item]
    
    if random() < 0.5 and len(knapsack.items) > 0:
        # Remove a random item
        item = choice(knapsack.items)
        if item not in mutated.remove_items:
            mutated.remove_items.append(item)
            # Remove conflicting items from add_items
            mutated.add_items = [a for a in mutated.add_items if a != item]
    
    # Randomly remove some items from the movement
    if random() < 0.3 and len(mutated.add_items) > 0:
        mutated.add_items.pop(randint(0, len(mutated.add_items) - 1))
    
    if random() < 0.3 and len(mutated.remove_items) > 0:
        mutated.remove_items.pop(randint(0, len(mutated.remove_items) - 1))
    
    return mutated


def _is_valid_movement(movement, knapsack):
    """Check if a movement is valid (can be executed on the knapsack)."""
    # Check if all remove_items are in the knapsack
    for item in movement.remove_items:
        if item not in knapsack:
            return False
    
    # Create a temporary knapsack to simulate the state after removals
    # Calculate what items would remain after removing items
    temp_items = [item for item in knapsack.items if item not in movement.remove_items]
    
    # Calculate available weight and volume after removing items
    temp_weight = knapsack.initial_weight
    temp_volume = knapsack.initial_volume
    for item in temp_items:
        temp_weight -= item.weight
        temp_volume -= item.volume
    
    # Create a temporary knapsack instance to use can_add_item
    # We'll manually set up its state without using add_item to avoid the all_items issue
    temp_all_items = deepcopy(knapsack.all_items)
    # Add items from movement.add_items that might not be in all_items yet
    for item in movement.add_items:
        # Check if this item (by value) is already in temp_all_items
        if not any(i.name == item.name and i.value == item.value and 
                   i.weight == item.weight and i.volume == item.volume 
                   for i in temp_all_items):
            temp_all_items.append(deepcopy(item))
    
    temp_knapsack = Knapsack(knapsack.initial_weight, knapsack.initial_volume, temp_all_items)
    
    # Manually set up the temp knapsack state (items that remain after removals)
    # Find corresponding items in temp_all_items and manually update knapsack state
    temp_knapsack_items = []
    for original_item in temp_items:
        # Find the corresponding item in temp_all_items
        for temp_item in temp_all_items:
            if (temp_item.name == original_item.name and 
                temp_item.value == original_item.value and
                temp_item.weight == original_item.weight and
                temp_item.volume == original_item.volume):
                temp_knapsack_items.append(temp_item)
                temp_knapsack.weight -= temp_item.weight
                temp_knapsack.volume -= temp_item.volume
                temp_knapsack.value += temp_item.value
                break
    
    temp_knapsack.items = temp_knapsack_items
    
    # Check if all add_items can be added using can_add_item
    # We need to check them sequentially and update the temp knapsack
    for original_item in movement.add_items:
        # Find the corresponding item in temp_all_items
        temp_item = None
        for item in temp_all_items:
            if (item.name == original_item.name and 
                item.value == original_item.value and
                item.weight == original_item.weight and
                item.volume == original_item.volume):
                temp_item = item
                break
        
        if temp_item is None:
            return False
            
        if not temp_knapsack.can_add_item(temp_item):
            return False
        # Manually update temp knapsack state to check subsequent items
        temp_knapsack.items.append(temp_item)
        temp_knapsack.weight -= temp_item.weight
        temp_knapsack.volume -= temp_item.volume
        temp_knapsack.value += temp_item.value
    
    return True