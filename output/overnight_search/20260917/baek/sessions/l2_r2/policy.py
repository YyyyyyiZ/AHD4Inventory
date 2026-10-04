import math
import numpy as np
from numba import njit


@njit
def _perishable_value_iteration(
    ages,
    totals,
    offsets,
    remove_oldest,
    remove_freshest,
    next_age_index,
    cap,
    fifo_weights,
    fifo_success,
    lifo_weights,
    lifo_success,
    has_fifo,
    has_lifo,
    waste_cost,
    holding_cost,
    lost_cost,
    iterations,
    discount,
):
    nstates = totals.size

    value = np.zeros((cap + 1, nstates), dtype=np.float64)
    new_value = np.empty_like(value)
    policy = np.zeros((cap + 1, nstates), dtype=np.uint8)

    terminal = np.empty(nstates, dtype=np.float64)
    after_lifo = np.empty(nstates, dtype=np.float64)
    after_fifo = np.empty(nstates, dtype=np.float64)
    component_0 = np.empty(nstates, dtype=np.float64)
    component_1 = np.empty(nstates, dtype=np.float64)

    for _ in range(iterations):
        new_value[:, :] = 1.0e100

        for pipe in range(cap + 1):
            for order in range(cap - pipe + 1):
                max_total = cap - pipe - order
                count = offsets[max_total + 1]

                for i in range(count):
                    terminal[i] = (
                        waste_cost * ages[i, 0]
                        + holding_cost * (totals[i] - ages[i, 0])
                        + discount * value[order, next_age_index[pipe, i]]
                    )

                if has_lifo:
                    p0 = lifo_success[0]
                    p1 = lifo_success[1]

                    component_0[0] = (
                        terminal[0] + lost_cost * (1.0 - p0) / p0
                    )
                    component_1[0] = (
                        terminal[0] + lost_cost * (1.0 - p1) / p1
                    )

                    for i in range(1, count):
                        component_0[i] = (
                            p0 * terminal[i]
                            + (1.0 - p0)
                            * component_0[remove_freshest[i]]
                        )
                        component_1[i] = (
                            p1 * terminal[i]
                            + (1.0 - p1)
                            * component_1[remove_freshest[i]]
                        )

                    for i in range(count):
                        after_lifo[i] = (
                            lifo_weights[0] * component_0[i]
                            + lifo_weights[1] * component_1[i]
                        )
                else:
                    for i in range(count):
                        after_lifo[i] = terminal[i]

                if has_fifo:
                    p0 = fifo_success[0]
                    p1 = fifo_success[1]

                    component_0[0] = (
                        after_lifo[0] + lost_cost * (1.0 - p0) / p0
                    )
                    component_1[0] = (
                        after_lifo[0] + lost_cost * (1.0 - p1) / p1
                    )

                    for i in range(1, count):
                        component_0[i] = (
                            p0 * after_lifo[i]
                            + (1.0 - p0)
                            * component_0[remove_oldest[i]]
                        )
                        component_1[i] = (
                            p1 * after_lifo[i]
                            + (1.0 - p1)
                            * component_1[remove_oldest[i]]
                        )

                    for i in range(count):
                        after_fifo[i] = (
                            fifo_weights[0] * component_0[i]
                            + fifo_weights[1] * component_1[i]
                        )
                else:
                    for i in range(count):
                        after_fifo[i] = after_lifo[i]

                for i in range(count):
                    candidate = after_fifo[i]
                    if candidate < new_value[pipe, i] - 1.0e-10:
                        new_value[pipe, i] = candidate
                        policy[pipe, i] = order

        if discount == 1.0:
            reference = new_value[0, 0]
            for pipe in range(cap + 1):
                count = offsets[cap - pipe + 1]
                for i in range(count):
                    new_value[pipe, i] -= reference

        value, new_value = new_value, value

    return policy


def design(params):
    scenario = scenario_from_params(params)
    m = int(scenario.m)
    cap = int(inventory_cap(scenario))

    rows = []

    def enumerate_compositions(prefix, dimensions, remaining):
        if dimensions == 1:
            rows.append(prefix + [remaining])
            return
        for quantity in range(remaining + 1):
            enumerate_compositions(
                prefix + [quantity], dimensions - 1, remaining - quantity
            )

    for total in range(cap + 1):
        enumerate_compositions([], m, total)

    ages = np.asarray(rows, dtype=np.int16)
    totals = ages.sum(axis=1).astype(np.int16)
    nstates = ages.shape[0]

    # States are sorted first by total inventory and then lexicographically.
    offsets = np.zeros(cap + 2, dtype=np.int32)
    for total in range(cap + 1):
        offsets[total + 1] = (
            offsets[total] + math.comb(total + m - 1, m - 1)
        )

    choose = np.zeros((cap + m + 2, m + 2), dtype=np.int64)
    for n in range(choose.shape[0]):
        for k in range(min(n, m + 1) + 1):
            choose[n, k] = math.comb(n, k)

    def rank_age(age_vector):
        total = 0
        for quantity in age_vector:
            total += int(quantity)

        rank = int(offsets[total])
        remaining = total

        for j in range(m - 1):
            tail_dimensions = m - j - 1
            quantity = int(age_vector[j])
            rank += int(
                choose[remaining + tail_dimensions, tail_dimensions]
                - choose[
                    remaining - quantity + tail_dimensions,
                    tail_dimensions,
                ]
            )
            remaining -= quantity

        return rank

    remove_oldest = np.zeros(nstates, dtype=np.int32)
    remove_freshest = np.zeros(nstates, dtype=np.int32)
    next_age_index = np.zeros((cap + 1, nstates), dtype=np.int32)

    for i in range(nstates):
        age = ages[i]

        if totals[i] > 0:
            reduced = age.copy()
            for j in range(m):
                if reduced[j] > 0:
                    reduced[j] -= 1
                    break
            remove_oldest[i] = rank_age(reduced)

            reduced = age.copy()
            for j in range(m - 1, -1, -1):
                if reduced[j] > 0:
                    reduced[j] -= 1
                    break
            remove_freshest[i] = rank_age(reduced)

        max_receipt = cap - int(totals[i])
        shifted = np.empty(m, dtype=np.int16)
        for j in range(m - 1):
            shifted[j] = age[j + 1]

        for receipt in range(max_receipt + 1):
            shifted[m - 1] = receipt
            next_age_index[receipt, i] = rank_age(shifted)

    def geometric_components(fraction):
        if fraction <= 0.0:
            return (
                np.array([0.5, 0.5], dtype=np.float64),
                np.array([1.0, 1.0], dtype=np.float64),
                False,
            )

        mean = fraction * float(scenario.mean)
        sd = (
            math.sqrt(fraction)
            * float(scenario.cv)
            * float(scenario.mean)
        )
        components = _aer_components(mean, sd)

        weights = np.zeros(2, dtype=np.float64)
        success = np.ones(2, dtype=np.float64)

        for k in range(min(2, len(components))):
            weights[k] = float(components[k][0])
            success[k] = float(components[k][1].args[-1])

        return weights, success, True

    fifo_weights, fifo_success, has_fifo = geometric_components(
        float(scenario.f)
    )
    lifo_weights, lifo_success, has_lifo = geometric_components(
        1.0 - float(scenario.f)
    )

    if has_fifo:
        iterations = 80
        discount = 1.0
    else:
        iterations = 500
        discount = 0.999

    action_table = _perishable_value_iteration(
        ages,
        totals,
        offsets,
        remove_oldest,
        remove_freshest,
        next_age_index,
        cap,
        fifo_weights,
        fifo_success,
        lifo_weights,
        lifo_success,
        has_fifo,
        has_lifo,
        float(scenario.w),
        float(scenario.h),
        float(scenario.p),
        iterations,
        discount,
    )

    def policy(age, pipeline):
        pipe = int(pipeline[0])
        return int(action_table[pipe, rank_age(age)])

    return policy
