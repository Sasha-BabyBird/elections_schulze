"""Тесты ядра Шульце. Запуск: pytest -q (из корня репозитория)."""
import io
import numpy as np
import pandas as pd
import pytest
from sspmpu_elections import Elections, determine_winners, compute_elections
from sspmpu_elections.schulze_utils import base_relation


def _elections_from_arrays(names, ranks, years, common, courses=None):
    courses = courses or [1] * len(names)
    cand = pd.DataFrame({'№': range(1, len(names) + 1), 'Фамилия': names, 'Курс': courses})
    cols = ['№'] + names
    rows = [[i + 1] + list(r) for i, r in enumerate(ranks)]
    bal = pd.DataFrame(rows, columns=cols)
    cb = io.StringIO(); cand.to_csv(cb, sep=';', index=False); cb.seek(0)
    bb = io.StringIO(); bal.to_csv(bb, sep=';', index=False); bb.seek(0)
    return Elections(cb, bb, complete=False, years=years, common=common)


def _random_profile(nc, nb, seed):
    rng = np.random.default_rng(seed)
    names = [f'c{i}' for i in range(nc)]
    ranks = [list(rng.permutation(nc) + 1) for _ in range(nb)]
    return _elections_from_arrays(names, ranks, years=[1], common=1), names


# --- эталон: независимый O(C^3) Шульце (winning votes), обнуляющий не-победы ---
def _ref_schulze_winner(N):
    C = N.shape[0]
    d = np.where(N > N.T, N, 0).astype(float)
    p = d.copy(); np.fill_diagonal(p, 0)
    for i in range(C):
        for j in range(C):
            if i != j:
                for kk in range(C):
                    if i != kk and j != kk:
                        p[j, kk] = max(p[j, kk], min(p[j, i], p[i, kk]))
    return [i for i in range(C) if all(p[i, j] >= p[j, i] for j in range(C) if j != i)]


def test_canonical_schulze_example():
    prefs = [(5, 'ACBED'), (5, 'ADECB'), (8, 'BEDAC'), (3, 'CABED'),
             (7, 'CAEBD'), (2, 'CBADE'), (7, 'DCEBA'), (8, 'EBADC')]
    names = list('abcde'); ranks = []
    for cnt, order in prefs:
        rmap = {ch.lower(): i + 1 for i, ch in enumerate(order)}
        ranks += [[rmap[n] for n in names]] * cnt
    e = _elections_from_arrays(names, ranks, years=[1], common=1)
    assert determine_winners(e.ballots_matrix, e.pairwise_matrix, 1, silent=True) == ['e']


def test_condorcet_winner_always_elected():
    tested = 0
    for s in range(60):
        e, names = _random_profile(6, 41, s)
        N = e.pairwise_matrix.to_numpy(); C = 6
        cw = [i for i in range(C) if all(N[i, j] > N[j, i] for j in range(C) if j != i)]
        if cw:
            tested += 1
            w = determine_winners(e.ballots_matrix, e.pairwise_matrix, 1, silent=True)[0]
            assert w == names[cw[0]]
    assert tested > 10


def test_matches_reference_on_unique_winner():
    for s in range(60):
        e, names = _random_profile(7, 41, s)
        N = e.pairwise_matrix.to_numpy()
        ref = _ref_schulze_winner(N)
        if len(ref) == 1:                       # единственный победитель Шульце
            w = determine_winners(e.ballots_matrix, e.pairwise_matrix, 1, silent=True)[0]
            assert w == names[ref[0]]


def test_determinism_same_seed():
    e, _ = _random_profile(8, 40, seed=3)       # чётное число -> вероятны ничьи
    runs = [tuple(determine_winners(e.ballots_matrix, e.pairwise_matrix, 1, silent=True, seed=7))
            for _ in range(5)]
    assert len(set(runs)) == 1                  # один seed -> один результат


def test_always_returns_k_winners():
    e, names = _random_profile(8, 40, seed=11)
    for k in range(1, 9):
        w = determine_winners(e.ballots_matrix, e.pairwise_matrix, k, silent=True)
        assert len(w) == k and len(set(w)) == k


def test_cutline_tie_resolves_to_exactly_k():
    # 4 кандидата, идеально симметричный цикл a>b>c>d>a при равных силах: жёсткая ничья
    names = list('abcd')
    base = [[1, 2, 3, 4], [4, 1, 2, 3], [3, 4, 1, 2], [2, 3, 4, 1]]
    e = _elections_from_arrays(names, base * 3, years=[1], common=1)
    for k in (1, 2, 3):
        w = determine_winners(e.ballots_matrix, e.pairwise_matrix, k, silent=True, seed=0)
        assert len(w) == k and len(set(w)) == k


@pytest.mark.parametrize("ex,k,must,mustnot", [('5', 2, 'a', 'b'), ('11', 3, 'a', 'c'), ('12', 2, 'a', 'c')])
def test_documented_examples_invariants(ex, k, must, mustnot):
    yrs = [] if ex == '12' else [1]
    e = Elections(f'examples/candidates_ex{ex}.csv', f'examples/ballots_ex{ex}.csv',
                  complete=False, years=yrs, common=k)
    w = determine_winners(e.ballots_matrix, e.pairwise_matrix, k, silent=True, seed=0)
    assert must in w and mustnot not in w


def test_duplicate_surname_rejected():
    with pytest.raises(ValueError):
        _elections_from_arrays(['a', 'a', 'b'], [[1, 2, 3], [3, 1, 2]], years=[1], common=1)


def test_full_election_runs():
    e = _elections_from_arrays(list('abcdefg'), [list(np.roll(range(1, 8), i)) for i in range(7)] * 4,
                               years=[1, 5], common=3, courses=[1, 1, 1, 5, 1, 1, 2])
    members = compute_elections(e, silent=True, seed=0)
    assert members is not None and len(members) == len(set(members))
