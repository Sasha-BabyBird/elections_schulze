import datetime
import pytz
from .schulze_utils import *


def determine_winners(ballots_matrix, pairwise_matrix, winners_to_determine=1, compare_method="wins", report_file=None, silent=False):
    """
    Аргументы:
    ballots_matrix - список бюллетеней в виде Pandas DataFrame.
    pairwise_matrix - матрица попарных предпочтений, или матрица Кондорсе, Pandas DataFrame.
    winners_to_determine - количество определяемых победителей, int.
    compare_method - "wins", "losses", "margins", "ratios" - способ сравнения силы звеньев. 
    Если все голосующие обязаны ранжировать всех кандидатов по-разному, то четыре способа
    дают идентичный результат. 
    Возвращает список победителей, полученный либо непосредственным применением
    метода Шульце, либо после разрешения ничейных ситуаций, list.
    """

    def handle_output(text, report_file=report_file, silent=silent):
        if report_file is not None:
            with open(report_file, 'a', encoding='windows-1251') as fl:
                fl.write('\n' + text)
        if not silent:
            print(text)

    list_of_candidates = pairwise_matrix.index.to_list()
    num_of_candidates = len(list_of_candidates)
    links_order = get_links_order(pairwise_matrix, compare_method)
    paths_matrix = get_paths_matrix_by_links_order(links_order, list_of_candidates)
    rel = get_binary_relation(links_order, paths_matrix)

    handle_output(f'Таблица попарных предпочтений:\n{pairwise_matrix.to_string()}')
    numeric_paths_matrix = get_numeric_paths_matrix(pairwise_matrix, paths_matrix)
    handle_output(f'\nТаблица сильнейших путей:\n{numeric_paths_matrix.to_string()}')
    if num_of_candidates > 1:
        handle_output(f'\nБинарное отношение:\n{'\n'.join(numeric_binary_relation(numeric_paths_matrix, rel))}')

    result = get_winners_from_relation(rel, list_of_candidates, winners_to_determine)[0]
    if result:
        return result
    
    handle_output("Обнаружена ничейная ситуация!\n")
    squared_num = num_of_candidates**2
    bad_pairs_of_links = 0
    unpicked_ballots = ballots_matrix.copy()
    num_of_ballots = len(unpicked_ballots)
    for link_id in np.arange(squared_num):
            cur_row_index = links_order.index[link_id]
            for other_link_id in np.arange(squared_num):
                cur_col_index = links_order.index[other_link_id]
                # считаем все одинаковые по силе пары звеньев
                if (cur_row_index[0] != cur_row_index[1]) and (cur_col_index[0] != cur_col_index[1]) \
                    and (cur_row_index != cur_col_index) and links_order.iloc[link_id, other_link_id] == 0:
                    bad_pairs_of_links += 1
    if bad_pairs_of_links > 0:
        random_tiebreaker = True
        handle_output("Используем случайные бюллетени, чтобы разрешить ситуацию.\n")
    else:
        random_tiebreaker = False
    while bad_pairs_of_links: 
        if num_of_ballots == 0:
            break
        random_ballot = unpicked_ballots.iloc[np.random.randint(0, num_of_ballots)]
        handle_output(f"Извлечён случайный бюллетень №{random_ballot.name}.")
        unpicked_ballots.drop(random_ballot.name, inplace=True)
        num_of_ballots -= 1

        for link_id in np.arange(squared_num):
            cur_row_index = links_order.index[link_id]
            for other_link_id in np.arange(squared_num):
                cur_col_index = links_order.index[other_link_id]
                if (cur_row_index[0] != cur_row_index[1]) and (cur_col_index[0] != cur_col_index[1]) \
                    and (cur_row_index != cur_col_index) and links_order.iloc[link_id, other_link_id] == 0:
                    '''
                    Проверяем, есть ли среди двух одинаковых по силе звеньев те, которые противоречат
                    взаимному расположению кандидатов, составляющих звено, в бюллетене.
                    Если такое звено в паре ровно одно, то это можно использовать 
                    для разрешения ничейной ситуации.
                    '''
                    if (random_ballot.loc[cur_row_index[0]] < random_ballot.loc[cur_row_index[1]] \
                        and random_ballot.loc[cur_col_index[0]] > random_ballot.loc[cur_col_index[1]]):
                        links_order.iloc[link_id, other_link_id] = 1
                        links_order.iloc[other_link_id, link_id] = -1
                        bad_pairs_of_links -= 2

                    elif (random_ballot.loc[cur_row_index[0]] > random_ballot.loc[cur_row_index[1]] \
                        and random_ballot.loc[cur_col_index[0]] < random_ballot.loc[cur_col_index[1]]):
                        links_order.iloc[link_id, other_link_id] = -1
                        links_order.iloc[other_link_id, link_id] = 1
                        bad_pairs_of_links -= 2

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
    paths_matrix_with_forbidden_links = new_paths_matrix.copy()
    forbidden = np.empty((num_of_candidates, num_of_candidates), dtype=bool)
    forbidden.fill(False)
    forbidden = pd.DataFrame(forbidden, index=pairwise_matrix.index, columns=pairwise_matrix.columns)
    tiebreaking_relation = set()
    for candidate_id in np.arange(unpicked):
        for opponent_id in np.arange(candidate_id + 1, unpicked):
            if paths_matrix_with_forbidden_links.at[unpicked_candidates[candidate_id], unpicked_candidates[opponent_id]] == \
            paths_matrix_with_forbidden_links.at[unpicked_candidates[opponent_id], unpicked_candidates[candidate_id]]:
                for p in np.arange(num_of_candidates):
                    for q in np.arange(num_of_candidates):
                        if p != q:
                            forbidden.iat[p, q] = False
                broken_tie = False
                """
                Для каждой неранжируемой пары кандидатов
                используется свой набор запрещаемых звеньев.
                """ 
                while not broken_tie:
                    bad_link = new_paths_matrix.at[unpicked_candidates[candidate_id], unpicked_candidates[opponent_id]]
                    forbidden.at[bad_link[0], bad_link[1]] = True
                    for p in np.arange(num_of_candidates):
                        for q in np.arange(num_of_candidates):
                            if p != q and forbidden.iat[p, q]:
                                paths_matrix_with_forbidden_links.iat[p, q] = 'worst'
                            elif p != q:
                                paths_matrix_with_forbidden_links.iat[p, q] = (list_of_candidates[p], list_of_candidates[q])
                    for p in np.arange(num_of_candidates):
                        for q in np.arange(num_of_candidates):
                            for k in np.arange(num_of_candidates):
                                if p != q and k not in (p, q):
                                    if links_order.at[(paths_matrix_with_forbidden_links.iat[q, p]), (paths_matrix_with_forbidden_links.iat[p, k])] <= 0:
                                        min_of_two = paths_matrix_with_forbidden_links.iat[q, p]
                                    else:
                                        min_of_two = paths_matrix_with_forbidden_links.iat[p, k]
                                    if links_order.at[(paths_matrix_with_forbidden_links.iat[q, k]), (min_of_two)] == -1:
                                        paths_matrix_with_forbidden_links.iat[q,k] = min_of_two

                    tie_status = links_order.at[paths_matrix_with_forbidden_links.at[unpicked_candidates[candidate_id], unpicked_candidates[opponent_id]], \
                    paths_matrix_with_forbidden_links.at[unpicked_candidates[opponent_id], unpicked_candidates[candidate_id]]]
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
                    elif paths_matrix_with_forbidden_links.at[unpicked_candidates[candidate_id], unpicked_candidates[opponent_id]] != 'worst':
                        broken_tie = False
    #print(paths_matrix_with_forbidden_links)
    #print(forbidden)
    handle_output(f'\nТаблица сильнейших путей, финальная:\n{paths_matrix_with_forbidden_links.to_string()}')
    handle_output(f'\nБинарное отношение, финальное:\n{tiebreaking_relation | sigma_relation}')

    unpicked_candidates = set(unpicked_candidates)
    for k in np.arange(unpicked):
        current_possible_winners = set(unpicked_candidates)
        for candidate in unpicked_candidates:
            for opponent in unpicked_candidates:
                if candidate != opponent and (candidate, opponent) in tiebreaking_relation:
                    current_possible_winners.discard(opponent)
        if len(current_possible_winners) > 1:
           return None
        new_winner = current_possible_winners.pop()
        full_order[k + seats_to_determine_start_with] = new_winner
        unpicked_candidates.discard(new_winner)
    result = [full_order[i + 1] for i in np.arange(winners_to_determine)]
    return result
    

def compute_elections(elections, compare_method="wins", report_file=None, silent=False):
    """
    Основная функция, выводящая информацию о подсчёте голосов.
    Аргументы:
    elections - экземпляр класса Elections.
    compare_method - "wins", "losses", "margins", "ratios" - способ сравнения силы звеньев. 
    Если все голосующие обязаны ранжировать всех кандидатов по-разному, то четыре способа
    дают идентичный результат. 
    Возвращает список избранных членов Студсовета, int.
    """
    def handle_output(text, report_file=report_file, silent=silent):
        if report_file is not None:
            with open(report_file, 'a', encoding='windows-1251') as fl:
                fl.write('\n' + text)
        if not silent:
            print(text)

    if report_file is not None:
        with open(report_file, 'a', encoding='windows-1251') as f:
            f.write('\n' + str(datetime.datetime.now(pytz.timezone('Europe/Moscow'))) + '\n')

    years_printable = {1: '1 курса бакалавриата', 2: '2 курса бакалавриата', 3: '3 курса бакалавриата', 
                       4: '4 курса бакалавриата', 5: '1 курса магистратуры', 6: '2 курса магистратуры'}
    
    handle_output(f"Выборы в Студенческий совет факультета ПМ-ПУ проводятся на " + 
          f"{len(elections.years) + elections.common} вакантных мест,\nиз которых " + 
          f"{elections.common} являются общими вакантными местами,\nа {len(elections.years)}" + 
          f" — местами для представителей курсов:\n")
    handle_output(f"{',\n'.join(years_printable[year] for year in elections.years)}.\n")
    handle_output(f"Список кандидатов:\n{'.\n'.join(str(ind) + '. ' + cand.iloc[0] \
          + ', ' + re.sub('курса', 'курс', years_printable[cand.iloc[1]]) \
          for ind, cand in elections.candidates.iterrows())}.\n")
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
            winner = determine_winners(elections.ballots_matrix, matrix, winners_to_determine=1, compare_method=compare_method, report_file=report_file, silent=silent)[0]
            if winner is None:
                handle_output("Произошла ошибка. Не удается найти уникального победителя!")
                return
            handle_output(f"\nПобедитель от {years_printable[year]}:\n{winner}\n")
            all_members.append(winner)
            common_matrix.drop(index=winner, inplace=True)
            common_matrix.drop(columns=winner, inplace=True)
    common_seats = elections.common + additional_seats
    common_winners = determine_winners(elections.ballots_matrix, common_matrix, winners_to_determine=common_seats, compare_method=compare_method, report_file=report_file, silent=silent)
    if common_winners is None:
        handle_output("Произошла ошибка. Не удается найти уникального победителя!")
        return
    handle_output(f"\nПобедители в конкурсе на общие вакантные места (порядок может не отражать занятые места):\n{'.\n'.join(str(i+1) + '. ' + winner for i, winner in enumerate(common_winners))}.\n")
    for winner in common_winners:
        all_members.append(winner)
    handle_output(f"Поздравляем новых членов Студенческого совета ПМ-ПУ!\n{'.\n'.join(str(i+1) + '. ' + winner for i, winner in enumerate(all_members))}.\n\n")
    return all_members