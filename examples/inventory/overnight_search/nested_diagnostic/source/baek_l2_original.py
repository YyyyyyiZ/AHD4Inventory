import math
import itertools
import numpy as np


def solve(v, price, v0, vi0, gamma, cap):
    v = np.asarray(v, dtype=float)
    price = np.asarray(price, dtype=float)
    vi0 = np.asarray(vi0, dtype=float)
    gamma = np.asarray(gamma, dtype=float)

    m, n = v.shape
    result0 = np.zeros((m, n), dtype=int)
    if n == 0:
        return result0

    if cap is None:
        cardinality = n
    else:
        cardinality = max(0, min(n, int(cap)))
    if cardinality == 0:
        return result0

    weighted_revenue = v * price
    rng = np.random.default_rng(246813579)
    pools = [dict() for _ in range(m)]

    def scalar_metrics(i, selection):
        W = float(np.sum(v[i, selection]))
        A = float(np.sum(weighted_revenue[i, selection]))
        V = float(vi0[i] + W)
        if V <= 0.0:
            return 0.0, 0.0
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            D = float(V ** gamma[i])
            N = float(A * V ** (gamma[i] - 1.0))
        if not np.isfinite(D):
            D = np.finfo(float).max
        if not np.isfinite(N):
            N = np.sign(A) * np.finfo(float).max if A != 0 else 0.0
        return N, D

    def add_to_pool(i, selection):
        selection = np.asarray(selection, dtype=bool)
        key = np.packbits(selection).tobytes()
        if key not in pools[i]:
            N, D = scalar_metrics(i, selection)
            pools[i][key] = (selection.copy(), N, D)

    for i in range(m):
        add_to_pool(i, np.zeros(n, dtype=bool))

    # For modest numbers of feasible subsets, construct the exact upper
    # envelope of each nest's alternatives.
    exact_limit = 400000
    subset_count = 0
    exact_possible = True
    try:
        for k in range(cardinality + 1):
            subset_count += math.comb(n, k)
            if subset_count > exact_limit:
                exact_possible = False
                break
    except Exception:
        exact_possible = False

    if exact_possible:
        try:
            combinations = [np.empty((1, 0), dtype=np.int16)]
            for k in range(1, cardinality + 1):
                combinations.append(
                    np.asarray(list(itertools.combinations(range(n), k)),
                               dtype=np.int16)
                )

            for i in range(m):
                Ns = []
                Ds = []
                offsets = [0]

                for k, comb in enumerate(combinations):
                    if k == 0:
                        W = np.zeros(1, dtype=float)
                        A = np.zeros(1, dtype=float)
                    else:
                        W = np.sum(v[i, comb], axis=1)
                        A = np.sum(weighted_revenue[i, comb], axis=1)

                    V = vi0[i] + W
                    Nvals = np.zeros_like(V)
                    Dvals = np.zeros_like(V)
                    positive = V > 0.0
                    with np.errstate(over="ignore", under="ignore",
                                     invalid="ignore", divide="ignore"):
                        Dvals[positive] = V[positive] ** gamma[i]
                        Nvals[positive] = (
                            A[positive] * V[positive] ** (gamma[i] - 1.0)
                        )
                    Ns.append(Nvals)
                    Ds.append(Dvals)
                    offsets.append(offsets[-1] + len(V))

                Nall = np.concatenate(Ns)
                Dall = np.concatenate(Ds)
                if not (np.all(np.isfinite(Nall)) and
                        np.all(np.isfinite(Dall))):
                    raise ArithmeticError

                # Lines are N-zD. Sort by increasing line slope -D and
                # retain their upper envelope.
                order = np.lexsort((-Nall, -Dall))
                hull = []
                starts = []

                for idx0 in order:
                    idx = int(idx0)
                    if hull and Dall[idx] == Dall[hull[-1]]:
                        continue

                    while hull:
                        previous = hull[-1]
                        denominator = Dall[previous] - Dall[idx]
                        if denominator <= 0.0:
                            break
                        crossing = (
                            (Nall[previous] - Nall[idx]) / denominator
                        )
                        if len(hull) == 1 or crossing > starts[-1]:
                            break
                        hull.pop()
                        starts.pop()

                    if not hull:
                        crossing = -np.inf
                    hull.append(idx)
                    starts.append(crossing)

                for idx in hull:
                    k = int(np.searchsorted(offsets[1:], idx, side="right"))
                    row = idx - offsets[k]
                    selection = np.zeros(n, dtype=bool)
                    if k:
                        selection[combinations[k][row]] = True
                    add_to_pool(i, selection)

            def optimize_over_pools(initial_z=0.0):
                z = float(initial_z)
                chosen = None
                Ntotal = 0.0
                Dtotal = float(v0)

                for _ in range(100):
                    chosen = []
                    Ntotal = 0.0
                    Dtotal = float(v0)
                    for ii in range(m):
                        alternatives = list(pools[ii].values())
                        scores = np.asarray(
                            [x[1] - z * x[2] for x in alternatives]
                        )
                        alternative = alternatives[int(np.argmax(scores))]
                        chosen.append(alternative)
                        Ntotal += alternative[1]
                        Dtotal += alternative[2]

                    new_z = Ntotal / Dtotal if Dtotal > 0.0 else 0.0
                    if abs(new_z - z) <= 1e-12 * (1.0 + abs(z)):
                        z = new_z
                        break
                    z = new_z

                # Re-select at the final fractional parameter.
                chosen = []
                Ntotal = 0.0
                Dtotal = float(v0)
                for ii in range(m):
                    alternatives = list(pools[ii].values())
                    scores = np.asarray(
                        [x[1] - z * x[2] for x in alternatives]
                    )
                    alternative = alternatives[int(np.argmax(scores))]
                    chosen.append(alternative)
                    Ntotal += alternative[1]
                    Dtotal += alternative[2]

                revenue = Ntotal / Dtotal if Dtotal > 0.0 else 0.0
                return revenue, chosen

            _, chosen = optimize_over_pools()
            return np.asarray([x[0] for x in chosen], dtype=int)

        except Exception:
            # The heuristic below also handles unusual numerical cases.
            pass

    def nest_value(i, W, A, z):
        V = vi0[i] + W
        with np.errstate(over="ignore", under="ignore",
                         invalid="ignore", divide="ignore"):
            ans = V ** (gamma[i] - 1.0) * A - z * V ** gamma[i]
        if np.ndim(ans) == 0:
            if V <= 0.0:
                return 0.0
            if np.isnan(ans):
                return -np.inf
            return float(ans)
        ans = np.asarray(ans, dtype=float)
        ans = np.where(V > 0.0, ans, 0.0)
        ans = np.where(np.isnan(ans), -np.inf, ans)
        return ans

    def hill_climb(i, z, selection):
        w = v[i]
        wr = weighted_revenue[i]
        selection = np.asarray(selection, dtype=bool).copy()
        W = float(np.sum(w[selection]))
        A = float(np.sum(wr[selection]))
        current = nest_value(i, W, A, z)

        for _ in range(n + 5):
            best = current
            move = None
            inside = np.flatnonzero(selection)
            outside = np.flatnonzero(~selection)

            if inside.size:
                values = nest_value(
                    i, W - w[inside], A - wr[inside], z
                )
                q = int(np.argmax(values))
                if values[q] > best + 1e-12 * (1.0 + abs(best)):
                    best = float(values[q])
                    move = (0, int(inside[q]))

            if inside.size < cardinality and outside.size:
                values = nest_value(
                    i, W + w[outside], A + wr[outside], z
                )
                q = int(np.argmax(values))
                if values[q] > best + 1e-12 * (1.0 + abs(best)):
                    best = float(values[q])
                    move = (1, int(outside[q]))

            if inside.size and outside.size:
                WW = W - w[inside, None] + w[outside]
                AA = A - wr[inside, None] + wr[outside]
                values = nest_value(i, WW, AA, z)
                q = np.unravel_index(int(np.argmax(values)), values.shape)
                if values[q] > best + 1e-12 * (1.0 + abs(best)):
                    best = float(values[q])
                    move = (2, int(inside[q[0]]), int(outside[q[1]]))

            if move is None:
                break

            if move[0] == 0:
                j = move[1]
                selection[j] = False
                W -= w[j]
                A -= wr[j]
            elif move[0] == 1:
                j = move[1]
                selection[j] = True
                W += w[j]
                A += wr[j]
            else:
                j, k = move[1], move[2]
                selection[j] = False
                selection[k] = True
                W += w[k] - w[j]
                A += wr[k] - wr[j]
            current = best

        return current, selection

    def pair_escape(i, z, selection):
        best, selection = hill_climb(i, z, selection)
        w = v[i]
        wr = weighted_revenue[i]

        for _ in range(2):
            inside = np.flatnonzero(selection)
            outside = np.flatnonzero(~selection)
            W = float(np.sum(w[inside]))
            A = float(np.sum(wr[inside]))
            move = None
            candidate_best = best

            if inside.size + 2 <= cardinality and outside.size >= 2:
                p, q = np.triu_indices(outside.size, 1)
                j, k = outside[p], outside[q]
                values = nest_value(
                    i, W + w[j] + w[k], A + wr[j] + wr[k], z
                )
                loc = int(np.argmax(values))
                if values[loc] > candidate_best + 1e-12 * (
                    1.0 + abs(candidate_best)
                ):
                    candidate_best = float(values[loc])
                    move = (0, int(j[loc]), int(k[loc]))

            if inside.size >= 2:
                p, q = np.triu_indices(inside.size, 1)
                j, k = inside[p], inside[q]
                values = nest_value(
                    i, W - w[j] - w[k], A - wr[j] - wr[k], z
                )
                loc = int(np.argmax(values))
                if values[loc] > candidate_best + 1e-12 * (
                    1.0 + abs(candidate_best)
                ):
                    candidate_best = float(values[loc])
                    move = (1, int(j[loc]), int(k[loc]))

            if inside.size >= 2 and outside.size >= 2:
                ip, iq = np.triu_indices(inside.size, 1)
                op, oq = np.triu_indices(outside.size, 1)
                ri, rj = inside[ip], inside[iq]
                ai, aj = outside[op], outside[oq]

                remove_w = w[ri] + w[rj]
                remove_a = wr[ri] + wr[rj]
                add_w = w[ai] + w[aj]
                add_a = wr[ai] + wr[aj]

                WW = W - remove_w[:, None] + add_w
                AA = A - remove_a[:, None] + add_a
                values = nest_value(i, WW, AA, z)
                loc = np.unravel_index(int(np.argmax(values)), values.shape)
                if values[loc] > candidate_best + 1e-12 * (
                    1.0 + abs(candidate_best)
                ):
                    candidate_best = float(values[loc])
                    move = (
                        2, int(ri[loc[0]]), int(rj[loc[0]]),
                        int(ai[loc[1]]), int(aj[loc[1]])
                    )

            if move is None:
                break

            if move[0] == 0:
                selection[move[1]] = True
                selection[move[2]] = True
            elif move[0] == 1:
                selection[move[1]] = False
                selection[move[2]] = False
            else:
                selection[move[1]] = False
                selection[move[2]] = False
                selection[move[3]] = True
                selection[move[4]] = True

            best, selection = hill_climb(i, z, selection)

        return best, selection

    def optimize_nest(i, z):
        w = v[i]
        r = price[i]
        wr = weighted_revenue[i]
        g = gamma[i]

        # For gamma=1 the separated subproblem is linear and exact.
        if abs(g - 1.0) <= 1e-13:
            score = w * (r - z)
            order = np.argsort(-score, kind="stable")[:cardinality]
            count = int(np.sum(score[order] > 0.0))
            selection = np.zeros(n, dtype=bool)
            selection[order[:count]] = True
            add_to_pool(i, selection)
            return

        rmin = float(np.min(r))
        rmax = float(np.max(r))
        stationary_1 = g * z + (1.0 - g) * rmin
        stationary_2 = g * z + (1.0 - g) * rmax
        scale = max(1.0, abs(rmin), abs(rmax), abs(z),
                    abs(stationary_1), abs(stationary_2))
        low = min(0.0, rmin, z, stationary_1, stationary_2) - 0.5 * scale
        high = max(0.0, rmax, z, stationary_1, stationary_2) + 0.5 * scale

        thresholds = list(np.linspace(low, high, 61))
        thresholds.extend(r.tolist())
        thresholds.extend([z, stationary_1, stationary_2])

        intersections = []
        for k in range(n):
            denominator = w[k] - w[:k]
            tolerance = 1e-13 * np.maximum(
                1.0, np.maximum(abs(w[k]), np.abs(w[:k]))
            )
            valid = np.abs(denominator) > tolerance
            if np.any(valid):
                x = (
                    (wr[k] - wr[:k][valid]) / denominator[valid]
                )
                x = x[(x >= low) & (x <= high) & np.isfinite(x)]
                intersections.extend(x.tolist())

        if intersections:
            thresholds.extend(
                np.quantile(intersections, np.linspace(0.0, 1.0, 51)).tolist()
            )

        candidates = []
        for threshold in thresholds:
            score = wr - threshold * w
            order = np.argsort(-score, kind="stable")[:cardinality]
            cumulative_w = np.r_[0.0, np.cumsum(w[order])]
            cumulative_a = np.r_[0.0, np.cumsum(wr[order])]
            values = nest_value(i, cumulative_w, cumulative_a, z)
            take = np.argsort(values)[-3:]
            for k in take:
                candidates.append(
                    (float(values[k]), tuple(int(x) for x in order[:k]))
                )

        for alternative in pools[i].values():
            candidates.append(
                (alternative[1] - z * alternative[2],
                 tuple(int(x) for x in np.flatnonzero(alternative[0])))
            )

        candidates.sort(key=lambda x: x[0], reverse=True)
        seen = set()
        best_value = -np.inf
        best_selection = np.zeros(n, dtype=bool)

        for _, indices in candidates[:30]:
            key = tuple(sorted(indices))
            if key in seen:
                continue
            seen.add(key)
            selection = np.zeros(n, dtype=bool)
            if indices:
                selection[list(indices)] = True
            value, selection = hill_climb(i, z, selection)
            add_to_pool(i, selection)
            if value > best_value:
                best_value = value
                best_selection = selection.copy()

        # A few deterministic random restarts help with unsupported,
        # non-convex aggregate alternatives.
        for _ in range(4):
            k = int(rng.integers(0, cardinality + 1))
            selection = np.zeros(n, dtype=bool)
            if k:
                selection[rng.choice(n, size=k, replace=False)] = True
            value, selection = hill_climb(i, z, selection)
            add_to_pool(i, selection)
            if value > best_value:
                best_value = value
                best_selection = selection.copy()

        best_value, best_selection = pair_escape(
            i, z, best_selection
        )
        add_to_pool(i, best_selection)

    def optimize_over_current_pools(initial_z):
        z = float(initial_z)
        chosen = None

        for _ in range(60):
            chosen = []
            Ntotal = 0.0
            Dtotal = float(v0)

            for i in range(m):
                alternatives = list(pools[i].values())
                scores = np.asarray(
                    [x[1] - z * x[2] for x in alternatives], dtype=float
                )
                scores = np.where(np.isnan(scores), -np.inf, scores)
                alternative = alternatives[int(np.argmax(scores))]
                chosen.append(alternative)
                Ntotal += alternative[1]
                Dtotal += alternative[2]

            new_z = Ntotal / Dtotal if Dtotal > 0.0 else 0.0
            if not np.isfinite(new_z):
                new_z = z
            if abs(new_z - z) <= 1e-11 * (1.0 + abs(z)):
                z = new_z
                break
            z = new_z

        chosen = []
        Ntotal = 0.0
        Dtotal = float(v0)
        for i in range(m):
            alternatives = list(pools[i].values())
            scores = np.asarray(
                [x[1] - z * x[2] for x in alternatives], dtype=float
            )
            scores = np.where(np.isnan(scores), -np.inf, scores)
            alternative = alternatives[int(np.argmax(scores))]
            chosen.append(alternative)
            Ntotal += alternative[1]
            Dtotal += alternative[2]

        revenue = Ntotal / Dtotal if Dtotal > 0.0 else 0.0
        return revenue, z, chosen

    z = 0.0
    best_revenue = -np.inf
    best_solution = [np.zeros(n, dtype=bool) for _ in range(m)]
    max_outer = 60 if np.all(np.abs(gamma - 1.0) <= 1e-13) else 20

    for outer in range(max_outer):
        old_z = z
        for i in range(m):
            optimize_nest(i, z)

        revenue, z, chosen = optimize_over_current_pools(z)
        if revenue > best_revenue:
            best_revenue = revenue
            best_solution = [x[0].copy() for x in chosen]

        if outer >= 1 and abs(z - old_z) <= 1e-9 * (1.0 + abs(old_z)):
            break

    answer = np.asarray(best_solution, dtype=int)
    if cap is not None:
        # Defensive cap enforcement for unusual numerical inputs.
        for i in range(m):
            if np.sum(answer[i]) > cardinality:
                selected = np.flatnonzero(answer[i])
                answer[i, selected[cardinality:]] = 0
    return answer