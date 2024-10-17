#!/usr/bin/env python3

import time
import csv
import sys
import matplotlib.pyplot as plt
import numpy as np

def parse_cnf_csv(input_stream):
    # parse multiple CNF problems from a CSV input stream
    problems = []
    wff = []
    Nvars = 0
    Nclauses = 0

    csvFile = csv.reader(input_stream)
    for line in csvFile:
        # handle BOM and comments
        if line[0].startswith('\ufeff'):
            line[0] = line[0].replace('\ufeff', '')
        if line[0] == 'c':
            continue
        # if we are in the middle of a problem, store the previous one
        elif line[0] == 'p' and line[1] == 'cnf':
            if wff:
                problems.append((wff, Nvars, Nclauses))
                wff = []
            Nvars = int(line[2])
            Nclauses = int(line[3])
        # convert strings to integers and ignore empty columns
        else:
            clause = [int(lit) for lit in line if lit != '' and lit != '0']
            if clause:
                wff.append(clause)

    if wff:
        problems.append((wff, Nvars, Nclauses))

    return problems

def is_clause_satisfied(clause, assignment):
    """
    Checks if at least one literal in the clause is satisfied by the current assignment
    """
    for literal in clause:
        var = abs(literal)
        value = assignment.get(var)
        if literal > 0 and value == 1:
            return True                     # clause satisfied 
        elif literal < 0 and value == 0:    # clause satisfied
            return True
    return False                            # no literals satisfy the clause 

def incremental_sat(wff, Nvars, assignment, depth):
    """
    Tries to satisfy the wff incrementally by assigning values to variables and checking clauses
    - wff: The formula to check
    - Nvars: Number of variables
    - assignment: A dictionary holding variable assignments (1 for True, 0 for False)
    - depth: Current depth of recursion (which variable to assign next)
    """
    # Base Case: if all variables are assigned, check if the wff is satisfied
    if depth > Nvars:
        for clause in wff:
            if not is_clause_satisfied(clause, assignment):
                return False               # at least 1 clause is unsatisfied 
        return True                        # all clauses are satisfied

    # try assigning True (1) to the current variable
    assignment[depth] = 1
    if incremental_sat(wff, Nvars, assignment, depth + 1):
        return True                         # if this leads to a solution

    # backtrack and try assigning False (0) to the current variable
    assignment[depth] = 0
    if incremental_sat(wff, Nvars, assignment, depth + 1):
        return True                         # if this leads to a solution

    # neither True (1) nor False (0) led to a solution, so return False -> not satisfiable
    return False

def test_wff(wff, Nvars, Nclauses):
    """
    Tests a wff for satisfiability using incremental search and records execution time
    """
    assignment = {}                         # hold variable assignments 
    start = time.time()
    satisfiable = incremental_sat(wff, Nvars, assignment, 1)
    end = time.time()
    exec_time = int((end - start) * 1e6)    # execution time in microseconds
    return [assignment, satisfiable, exec_time]

def log_results(problem_index, Nvars, satisfiable, exec_time, assignment, output_stream):
    """
    Logs the result of each problem to the output stream with an enumerated problem number.
    
    Arguments:
    - problem_index: The enumerated index of the problem.
    - Nvars: The number of variables in the problem.
    - satisfiable: Boolean indicating if the problem is satisfiable.
    - exec_time: Time taken to solve the problem in microseconds.
    - assignment: The variable assignment that satisfies the problem (if applicable).
    - output_stream: The stream to write the output to (file or stdout).
    """
    result_str = f"{problem_index}: {Nvars} variables - Satisfiable: {satisfiable}, Time: {exec_time} microseconds\n"
    if satisfiable:
        result_str += f"Assignment: {assignment}\n"
    else:
        result_str += "No satisfying assignment found.\n"
    output_stream.write(result_str)


def plot_data(output_file_name):
    """
    Reads the output file and generates a plot with the number of variables (x-axis) vs execution time (y-axis).
    Green circles are used for satisfiable problems, red triangles for unsatisfiable.
    """
    num_vars = []
    exec_times = []
    satisfiability = []

    with open(output_file_name, 'r') as file:
        for line in file:
            # Skip lines that don't contain problem results
            if ": " not in line or "variables" not in line:
                continue

            # Parse the line that contains problem results
            parts = line.split()
            try:
                Nvars = int(parts[1])  # Number of variables
                exec_time = int(parts[-2])  # Execution time in microseconds
                # Check if the result says 'Satisfiable: True' or 'Satisfiable: False'
                is_satisfiable = 'True' in line  # This will now correctly check for 'True'

                num_vars.append(Nvars)
                exec_times.append(exec_time)
                satisfiability.append(is_satisfiable)
            except (ValueError, IndexError) as e:
                print(f"Error parsing line: {line}\n{e}")
                continue

    if not num_vars:
        print("No data found in the output file.")
        return

    # Plotting
    plt.figure(figsize=(10, 6))

    # Plot satisfiable and unsatisfiable problems
    satisfiable_x = [num_vars[i] for i in range(len(num_vars)) if satisfiability[i]]
    satisfiable_y = [exec_times[i] for i in range(len(num_vars)) if satisfiability[i]]
    unsatisfiable_x = [num_vars[i] for i in range(len(num_vars)) if not satisfiability[i]]
    unsatisfiable_y = [exec_times[i] for i in range(len(num_vars)) if not satisfiability[i]]

    plt.scatter(satisfiable_x, satisfiable_y, color='green', marker='o', label="Satisfiable")
    plt.scatter(unsatisfiable_x, unsatisfiable_y, color='red', marker='^', label="Unsatisfiable")

    # Plot 2^n line of best fit for unsatisfiable problems (O(2^n) complexity)
    max_n = max(num_vars)
    x_vals = np.arange(1, max_n + 1)
    y_vals = [2**n for n in x_vals]
    plt.plot(x_vals, y_vals, color='blue', linestyle='--', label="2^n Worst-case")

    # Add labels and title
    plt.xlabel('Number of Variables')
    plt.ylabel('Execution Time (microseconds)')
    plt.title('SAT Solver Performance: Number of Variables vs Execution Time')
    plt.legend(loc="upper left")

    # Save and show the plot
    plt.savefig('sat_solver_performance.png')
    plt.show()



def main():
    # parse command-line arguments
    program_name = sys.argv[0]
    input_file_name = sys.argv[1] if len(sys.argv) > 1 else None
    output_file_name = sys.argv[2] if len(sys.argv) > 2 else None

    # open input file or read from stdin
    if input_file_name:
        with open(input_file_name, "r") as input_file:
            problems = parse_cnf_csv(input_file)
    else:
        problems = parse_cnf_csv(sys.stdin)

    output_stream = open(output_file_name, "w") if output_file_name else sys.stdout

    # outputting the data
    try:
        output_stream.write(f"Program: {program_name}\n")
        output_stream.write(f"Input File: {input_file_name if input_file_name else 'stdin'}\n\n")

        for problem_index, (wff, Nvars, Nclauses) in enumerate(problems, start=1):
            results = test_wff(wff, Nvars, Nclauses)
            log_results(problem_index, Nvars, results[1], results[2], results[0], output_stream)
    finally:
        if output_stream is not sys.stdout:
            output_stream.close()

    # create graph from output file
    if output_file_name:
        plot_data(output_file_name)

if __name__ == "__main__":
    main()

