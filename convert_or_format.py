#!/usr/bin/env python3
"""
Script to convert OR format knapsack problem files to the format expected by this codebase.

OR Format:
- Line 1: num_constraints num_items
- Next lines: item values (num_items values, may span multiple lines)
- Next line: knapsack capacities (num_constraints values)
- Next lines: constraint 1 weights (num_items values, may span multiple lines)
- Next lines: constraint 2 weights (num_items values, may span multiple lines)
- ... (one set of weights per constraint)

Expected Format (for 2 constraints):
- Line 1: num_constraints num_items
- Line 2: all item values (one line)
- Line 3: capacities (2 values: weight capacity, volume capacity)
- Line 4: constraint 1 weights (all items, one line)
- Line 5: constraint 2 weights (all items, one line)
"""

import sys
import os


def read_numbers_from_lines(lines, start_idx, count):
    """Read a specified number of integers from lines, ignoring line breaks."""
    numbers = []
    current_idx = start_idx
    
    while len(numbers) < count and current_idx < len(lines):
        line = lines[current_idx].strip()
        if not line:
            current_idx += 1
            continue
        
        # Split by whitespace and convert to integers
        line_numbers = [int(x) for x in line.split()]
        numbers.extend(line_numbers)
        current_idx += 1
        
        if len(numbers) >= count:
            break
    
    return numbers[:count], current_idx


def convert_or_format(input_file, output_file):
    """Convert OR format file to expected format."""
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    if not lines:
        raise ValueError("Input file is empty")
    
    # Parse first line: num_constraints num_items
    first_line = lines[0].split()
    if len(first_line) < 2:
        raise ValueError("First line must contain num_constraints and num_items")
    
    num_constraints = int(first_line[0])
    num_items = int(first_line[1])
    
    print(f"Reading problem with {num_constraints} constraints and {num_items} items")
    
    # Read values (all items) - values may span multiple lines
    values, idx = read_numbers_from_lines(lines, 1, num_items)
    if len(values) != num_items:
        raise ValueError(f"Expected {num_items} values, got {len(values)}")
    print(f"  Read {len(values)} values starting from line {1}, ended at line {idx}")
    
    # Read capacities (one per constraint) - should be on a single line
    capacities, idx = read_numbers_from_lines(lines, idx, num_constraints)
    if len(capacities) != num_constraints:
        raise ValueError(f"Expected {num_constraints} capacities, got {len(capacities)}")
    print(f"  Read {len(capacities)} capacities starting from line {idx - 1}")
    
    # Require at least 2 constraints
    if num_constraints < 2:
        raise ValueError("This codebase requires at least 2 constraints")
    
    # Read constraint weights (one set per constraint)
    constraint_weights = []
    for constraint_idx in range(num_constraints):
        weights, idx = read_numbers_from_lines(lines, idx, num_items)
        if len(weights) != num_items:
            raise ValueError(f"Expected {num_items} weights for constraint {constraint_idx + 1}, got {len(weights)}")
        constraint_weights.append(weights)
    
    # Write in expected format
    with open(output_file, 'w') as f:
        # Line 1: num_constraints num_items
        f.write(f"{num_constraints} {num_items}\n")
        
        # Line 2: all values (one line) - must have exactly num_items columns
        if len(values) != num_items:
            raise ValueError(f"Values line must have exactly {num_items} columns, got {len(values)}")
        f.write(" ".join(str(v) for v in values) + "\n")
        
        # Line 3: capacities (all constraints)
        f.write(" ".join(str(c) for c in capacities) + "\n")
        
        # Lines 4 onwards: constraint weights (one line per constraint, each with exactly num_items columns)
        for constraint_idx in range(num_constraints):
            if len(constraint_weights[constraint_idx]) != num_items:
                raise ValueError(f"Constraint {constraint_idx + 1} weights line must have exactly {num_items} columns, got {len(constraint_weights[constraint_idx])}")
            f.write(" ".join(str(w) for w in constraint_weights[constraint_idx]) + "\n")
    
    print(f"Converted file written to: {output_file}")
    print(f"Format: {num_constraints} constraints, {num_items} items")
    print(f"Capacities: {' '.join(str(c) for c in capacities)}")
    print(f"Output {num_constraints} constraint lines, each with {num_items} columns")


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_or_format.py <input_file> [output_file]")
        print("  If output_file is not specified, it will be saved as <input_file>.converted")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Default output filename
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.converted"
    
    try:
        convert_or_format(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

