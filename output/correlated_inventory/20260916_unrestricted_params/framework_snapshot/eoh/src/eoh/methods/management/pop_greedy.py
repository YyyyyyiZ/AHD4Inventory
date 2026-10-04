import heapq
import math

def population_management(pop,size):
    #pop = [individual for individual in pop if individual['objective'] is not None]
    pop = [
        individual
        for individual in pop
        if individual['objective'] is not None
           and not math.isinf(individual['objective'])
    ]
    if size > len(pop):
        size = len(pop)
    unique_pop = []
    unique_objectives = []
    # Process in reverse order to keep the LAST (most recent) occurrence of each objective
    for individual in reversed(pop):
        if individual['objective'] not in unique_objectives:
            unique_pop.append(individual)
            unique_objectives.append(individual['objective'])
    # Reverse back to maintain original order
    unique_pop.reverse()
    # Delete the worst individual
    #pop_new = heapq.nsmallest(size, pop, key=lambda x: x['objective'])
    pop_new = heapq.nsmallest(size, unique_pop, key=lambda x: x['objective'])
    return pop_new