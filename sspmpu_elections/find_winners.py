import datetime
try:
    from zoneinfo import ZoneInfo            # стандартная библиотека (Python >= 3.9)
    def _now():
        return datetime.datetime.now(ZoneInfo('Europe/Moscow'))
except Exception:                            # pragma: no cover
    def _now():
        return datetime.datetime.now()

from .schulze_utils import *

REPORT_ENCODING = 'utf-8-sig'                # без потери кириллицы; корректно открывается Excel


def determine_winners(ballots_matrix, pairwise_matrix, winners_to_determine=1,
                      compare_method="wins", report_file=None, silent=False, seed=0):
    """
    Возвращает (неупорядоченный) список из winners_to_determine победителей по методу
    Шульце. Ничьи разрешаются ДЕТЕРМИНИРОВАННО по зафиксированному seed:
      1) базовый Шульце (быстрый путь O(C^3), без матрицы звеньев C^2 x C^2);
      2) иерархия случайных бюллетеней (для равных по силе звеньев) — как и раньше,
         но с засеянным ГСЧ;
      3) метод запрета звеньев (как и раньше, без изменений в логике);
      4) если осталась ничья — порядок по иерархии бюллетеней (новый страховочный шаг,
         гарантирует результат вместо возврата None).
    Всегда возвращает список длиной min(winners_to_determine, число кандидатов).
    """

    def handle_output(text, report_file=report_file, silent=silent):
        if report_file is not None:
            with open(report_file, 'a', encoding=REPORT_ENCODING) as fl:
                fl.write('\n' + text)
        if not silent:
            print(text)

    list_of_candidates = pairwise_matrix.index.to_list()
    num_of_candidates = len(list_of_candidates)
    winners_to_determine = min(winners_to_determine, num_of_candidates)
    sub_ballots = np.nan_to_num(ballots_matrix[list_of_candidates].to_numpy(dtype=float), nan=1e9)
    name_to_col = {name: i for i, name in enumerate(list_of_candidates)}
    rng = np.random.default_rng(seed)

    # --- БЫСТРЫЙ базовый путь: без построения матрицы звеньев C^2 x C^2 ---
    rel, P = base_relation(pairwise_matrix.to_numpy(), list_of_candidates, compare_method)
    numeric_paths_matrix = pd.DataFrame(
        np.where(np.isfinite(P), P, 0).astype(np.int64),
        index=list_of_candidates, columns=list_of_candidates)
    handle_output(f'Таблица попарных предпочтений:\n{pairwise_matrix.to_string()}')
    handle_output(f'\nТаблица сильнейших путей:\n{numeric_paths_matrix.to_string()}')
    if num_of_candidates > 1:
        rel_str = '\n'.join(numeric_binary_relation(numeric_paths_matrix, rel))
        handle_output(f'\nБинарное отношение:\n{rel_str}')

    result = get_winners_from_relation(rel, list_of_candidates, winners_to_determine)[0]
    if result:
        return result

    handle_output("Обнаружена ничейная ситуация!\n")
    # тяжёлые структуры строим ТОЛЬКО при ничьей; get_links_order теперь векторизован
    links_order = get_links_order(pairwise_matrix, compare_method)
    squared_num = num_of_candidates**2

    # --- иерархия случайных бюллетеней, ВЕКТОРИЗОВАНО ---
    # Семантика идентична прежнему поэлементному двойному циклу по парам звеньев,
    # но без pandas-доступа: для каждой пары РАВНЫХ по силе звеньев усиливаем то,
    # с которым согласен вытянутый бюллетень (если согласен ровно с одним из двух).
    lo = links_order.to_numpy().astype(np.int64)
    flat = np.arange(squared_num)
    offdiag = (flat // num_of_candidates) != (flat % num_of_candidates)   # звено (a, b) с a != b
    pair_mask = offdiag[:, None] & offdiag[None, :]
    np.fill_diagonal(pair_mask, False)                                    # исключаем то же самое звено

    def _count_bad(matrix):
        return int((pair_mask & (matrix == 0)).sum())

    bad_pairs_of_links = _count_bad(lo)
    unpicked_ballots = ballots_matrix.copy()
    num_of_ballots = len(unpicked_ballots)
    random_tiebreaker = bad_pairs_of_links > 0
    if random_tiebreaker:
        handle_output(f"Используем случайные бюллетени (seed={seed}), чтобы разрешить ситуацию.\n")
    while bad_pairs_of_links and num_of_ballots > 0:
        random_ballot = unpicked_ballots.iloc[int(rng.integers(0, num_of_ballots))]
        handle_output(f"Извлечён случайный бюллетень №{random_ballot.name}.")
        unpicked_ballots.drop(random_ballot.name, inplace=True)
        num_of_ballots -= 1
        br = random_ballot[list_of_candidates].to_numpy()
        agree = (br[:, None] < br[None, :]).ravel()      # бюллетень за (a выше b) для звена (a, b)
        disagree = (br[:, None] > br[None, :]).ravel()
        zero = pair_mask & (lo == 0)
        set_pos = zero & agree[:, None] & disagree[None, :]
        set_neg = zero & disagree[:, None] & agree[None, :]
        lo[set_pos] = 1
        lo[set_neg] = -1
        bad_pairs_of_links = _count_bad(lo)
    links_order = pd.DataFrame(lo, index=links_order.index, columns=links_order.columns)

    new_paths_matrix = get_paths_matrix_by_links_order(links_order, list_of_candidates)
    sigma_relation = get_binary_relation(links_order, new_paths_matrix)

    if random_tiebreaker:
        handle_output(f'\nТаблица сильнейших путей после попытки разрешить ничью:\n{new_paths_matrix.to_string()}')
        handle_output(f'\nБинарное отношение после попытки разрешить ничью:\n{sigma_relation}')

    result, full_order, unpicked_candidates = get_winners_from_relation(sigma_relation, list_of_candidates, winners_to_determine)
    if result:
        return result

    handle_output("Используем метод запрета звеньев, чтобы разрешить ситуацию.\n")
    seats_to_determine_start_with = 0
    for seat in np.arange(1, num_of_candidates+1):
        if seat not in full_order:
            seats_to_determine_start_with = seat
            break

    unpicked_candidates = list(unpicked_candidates)
    unpicked = len(unpicked_candidates)

    # фиктивное звено, которое заведомо слабее всех
    links_order.loc['worst'] = [-1]*squared_num
    links_order.loc[:, 'worst'] = [1]*squared_num + [0]
    # O(1)-доступ к сравнению силы звеньев вместо медленного pandas .at[(кортеж), (кортеж)].
    # Значения идентичны links_order; logic не меняется, меняется только способ чтения.
    _labels = list(itertools.product(list_of_candidates, list_of_candidates)) + ['worst']
    _LO = links_order.to_numpy()
    lo_get = {(_labels[i], _labels[j]): int(_LO[i, j])
              for i in range(len(_labels)) for j in range(len(_labels))}
    # Метод запрета звеньев — на numpy-массивах (доступ по позиции вместо pandas .iat/.at).
    # Управляющая логика и значения полностью совпадают с прежней реализацией.
    npm = new_paths_matrix.to_numpy()                 # критические звенья базовых путей (кортежи)
    pm = npm.copy()                                   # рабочая матрица (переносится между парами, как и раньше)
    fb = np.zeros((num_of_candidates, num_of_candidates), dtype=bool)
    idx = name_to_col
    tiebreaking_relation = set()
    for candidate_id in range(unpicked):
        for opponent_id in range(candidate_id + 1, unpicked):
            a = idx[unpicked_candidates[candidate_id]]
            b = idx[unpicked_candidates[opponent_id]]
            if pm[a, b] == pm[b, a]:
                fb[:] = False
                broken_tie = False
                """
                Для каждой неранжируемой пары кандидатов
                используется свой набор запрещаемых звеньев.
                """
                while not broken_tie:
                    bad_link = npm[a, b]
                    bli, blj = idx[bad_link[0]], idx[bad_link[1]]
                    if fb[bli, blj]:
                        # Это звено уже запрещено — прогресса не будет (в прежней версии здесь
                        # был бесконечный цикл: bad_link всегда брался из БАЗОВОЙ матрицы путей).
                        # Прекращаем; пара останется неразрешённой и попадёт в финальный
                        # детерминированный тай-брейк по иерархии бюллетеней.
                        break
                    fb[bli, blj] = True
                    for p in range(num_of_candidates):
                        for q in range(num_of_candidates):
                            if p != q:
                                pm[p, q] = 'worst' if fb[p, q] else (list_of_candidates[p], list_of_candidates[q])
                    for p in range(num_of_candidates):
                        for q in range(num_of_candidates):
                            for k in range(num_of_candidates):
                                if p != q and k not in (p, q):
                                    if lo_get[(pm[q, p], pm[p, k])] <= 0:
                                        min_of_two = pm[q, p]
                                    else:
                                        min_of_two = pm[p, k]
                                    if lo_get[(pm[q, k], min_of_two)] == -1:
                                        pm[q, k] = min_of_two
                    tie_status = lo_get[(pm[a, b], pm[b, a])]
                    """
                    Ничья между парами кандидатов разрешается, если удалось найти разные критические звенья для обоих путей,
                    или если все звенья были запрещены, что может произойти только в том случае,
                    если все голосующие поставили двум кандидатам одинаковые приоритеты.
                    """
                    broken_tie = True
                    if tie_status == 1:
                        tiebreaking_relation.add((unpicked_candidates[candidate_id], unpicked_candidates[opponent_id]))
                    elif tie_status == -1:
                        tiebreaking_relation.add((unpicked_candidates[opponent_id], unpicked_candidates[candidate_id]))
                    elif pm[a, b] != 'worst':
                        broken_tie = False
    paths_matrix_with_forbidden_links = pd.DataFrame(pm, index=pairwise_matrix.index, columns=pairwise_matrix.columns)

    handle_output(f'\nТаблица сильнейших путей, финальная:\n{paths_matrix_with_forbidden_links.to_string()}')
    handle_output(f'\nБинарное отношение, финальное:\n{tiebreaking_relation | sigma_relation}')

    # --- извлечение результата; при остаточной ничьей — детерминированный тай-брейк по иерархии ---
    remaining = set(unpicked_candidates)
    pos = seats_to_determine_start_with
    while remaining:
        current_possible_winners = set(remaining)
        for candidate in remaining:
            for opponent in remaining:
                if candidate != opponent and (candidate, opponent) in tiebreaking_relation:
                    current_possible_winners.discard(opponent)
        if len(current_possible_winners) == 1:
            new_winner = current_possible_winners.pop()
            full_order[pos] = new_winner
            remaining.discard(new_winner)
            pos += 1
        else:
            handle_output("Остаточная ничья — упорядочиваем по иерархии бюллетеней (seed).")
            order = rng.permutation(sub_ballots.shape[0])
            for name in candidate_hierarchy_sort(sorted(remaining), sub_ballots, name_to_col, order):
                full_order[pos] = name
                pos += 1
            remaining.clear()
    result = [full_order[i + 1] for i in range(winners_to_determine)]
    return result


def compute_elections(elections, compare_method="wins", report_file=None, silent=False, seed=0):
    """
    Основная процедура подсчёта. Сначала избираются представители курсов (по одному,
    метод Шульце), затем — общие места из оставшихся кандидатов.
    Возвращает список фамилий избранных членов Студсовета (list) либо None при ошибке.
    """
    def handle_output(text, report_file=report_file, silent=silent):
        if report_file is not None:
            with open(report_file, 'a', encoding=REPORT_ENCODING) as fl:
                fl.write('\n' + text)
        if not silent:
            print(text)

    if report_file is not None:
        with open(report_file, 'a', encoding=REPORT_ENCODING) as f:
            f.write('\n' + str(_now()) + '\n')

    years_printable = {1: '1 курса бакалавриата', 2: '2 курса бакалавриата', 3: '3 курса бакалавриата',
                       4: '4 курса бакалавриата', 5: '1 курса магистратуры', 6: '2 курса магистратуры'}

    handle_output(f"Выборы в Студенческий совет факультета ПМ-ПУ проводятся на " +
          f"{len(elections.years) + elections.common} вакантных мест,\nиз которых " +
          f"{elections.common} являются общими вакантными местами,\nа {len(elections.years)}" +
          f" — местами для представителей курсов:\n")
    nl = ',\n'
    dot_nl = '.\n'
    handle_output(f"{nl.join(years_printable[year] for year in elections.years)}.\n")
    cand_lines = dot_nl.join(
        f"{ind}. {cand.iloc[0]}, {re.sub('курса', 'курс', years_printable[cand.iloc[1]])}"
        for ind, cand in elections.candidates.iterrows())
    handle_output(f"Список кандидатов:\n{cand_lines}.\n")
    handle_output(f"Бюллетеней получено: {elections.num_of_ballots}.\n")
    handle_output("Ведём подсчёт голосов...\n")
    common_matrix = elections.pairwise_matrix.copy()
    additional_seats = 0
    all_members = []
    for year, matrix in elections.pairwise_matrices_by_years.items():
        if matrix.empty:
            handle_output(f"От {years_printable[year]} нет ни одного кандидата, место переходит в категорию общих вакантных.\n")
            additional_seats += 1
        else:
            winners = determine_winners(elections.ballots_matrix, matrix, winners_to_determine=1,
                                        compare_method=compare_method, report_file=report_file,
                                        silent=silent, seed=seed)
            if not winners:
                handle_output("Произошла ошибка. Не удаётся найти уникального победителя!")
                return None
            winner = winners[0]
            handle_output(f"\nПобедитель от {years_printable[year]}:\n{winner}\n")
            all_members.append(winner)
            common_matrix.drop(index=winner, inplace=True)
            common_matrix.drop(columns=winner, inplace=True)
    common_seats = elections.common + additional_seats
    common_winners = determine_winners(elections.ballots_matrix, common_matrix,
                                       winners_to_determine=common_seats, compare_method=compare_method,
                                       report_file=report_file, silent=silent, seed=seed)
    if not common_winners:
        handle_output("Произошла ошибка. Не удаётся найти победителей на общие места!")
        return None
    common_lines = dot_nl.join(f"{i+1}. {winner}" for i, winner in enumerate(common_winners))
    handle_output(f"\nПобедители в конкурсе на общие вакантные места (порядок может не отражать занятые места):\n{common_lines}.\n")
    all_members.extend(common_winners)
    members_lines = dot_nl.join(f"{i+1}. {member}" for i, member in enumerate(all_members))
    handle_output(f"Поздравляем новых членов Студенческого совета ПМ-ПУ!\n{members_lines}.\n\n")
    return all_members
