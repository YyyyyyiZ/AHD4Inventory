def parent_selection(population, m):
    """
    Deterministically select the top m parents with lowest objective values.

    Args:
        population: List of individuals with 'objective' field
        m: Number of parents to select

    Returns:
        List of m best parents (without replacement)
    """
    # Sort population by objective value (ascending - lower is better)
    # Use enumerate to preserve original order for tie-breaking
    indexed_pop = [(i, ind) for i, ind in enumerate(population)]
    sorted_pop = sorted(indexed_pop, key=lambda x: (x[1]['objective'], x[0]))

    # Select top m individuals (without replacement)
    n_select = min(m, len(population))
    parents = [ind for _, ind in sorted_pop[:n_select]]

    return parents
