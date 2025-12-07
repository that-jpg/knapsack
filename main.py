import sys
import os
from copy import deepcopy
from knapsack import *
from random import shuffle

def random_add_solution(knapsack):
    all_items = deepcopy(knapsack.all_items)    
    shuffle(all_items)
    for item in all_items:
        if knapsack.can_add_item(item):
            knapsack.add_item(item)
        else:
            continue

def items_from_file(filename):
    items = []
    with open(filename) as f:
        lines = f.readlines()
    lines = [line.strip().split(' ') for line in lines]
    numbers_of_items = int(lines[0][1])
    for i in range(numbers_of_items):
        item = Item("Item %d" % i, int(lines[1][i]), int(lines[3][i]), int(lines[4][i]))
        items.append(item)
    return items

def bag_constraints_from_file(filename):
    with open(filename) as f:
        lines = f.readlines()
    lines = [line.strip().split(' ') for line in lines]
    return int(lines[2][0]), int(lines[2][1])

def bag_from_file(filename):
    constraints = bag_constraints_from_file(filename)
    return (constraints[0], constraints[1], items_from_file(filename))

if __name__ == '__main__':
    data_folder = 'data'
    
    # Check if data folder exists
    if not os.path.exists(data_folder):
        print(f"Error: '{data_folder}' folder does not exist.")
        sys.exit(1)
    
    # Get all files from the data folder
    data_files = []
    for filename in os.listdir(data_folder):
        filepath = os.path.join(data_folder, filename)
        if os.path.isfile(filepath):
            data_files.append(filepath)
    
    if not data_files:
        print(f"Error: No files found in '{data_folder}' folder.")
        sys.exit(1)
    
    # Sort files for consistent processing order
    data_files.sort()
    
    print(f"Found {len(data_files)} file(s) in '{data_folder}' folder.")
    print("=" * 80)
    
    # Iterate through all data files
    for idx, data_file in enumerate(data_files, 1):
        print(f"\n{'=' * 80}")
        print(f"Processing file {idx}/{len(data_files)}: {data_file}")
        print(f"{'=' * 80}\n")
        
        try:
            bag = Knapsack(*bag_from_file(data_file), tabu_list=TabuList(200))
            bag.optimize(random_add_solution, TabuSearch(5), first_improving_neighborhood)
        except Exception as e:
            print(f"Error processing {data_file}: {e}")
            continue
    
    print(f"\n{'=' * 80}")
    print(f"Finished processing all {len(data_files)} file(s).")
    print(f"{'=' * 80}")
