import re
import itertools
import numpy as np
import pandas as pd

def compare_wins(pairwise_matrix, a, b, c, d):
    return pairwise_matrix.loc[a, b] > pairwise_matrix.loc[c, d]


def compare_margins(pairwise_matrix, a, b, c, d):
    return (pairwise_matrix.loc[a, b] - pairwise_matrix.loc[b, a]) > (pairwise_matrix.loc[c, d] - pairwise_matrix.loc[d, c])


def compare_ratios(pairwise_matrix, a, b, c, d):
    if pairwise_matrix.loc[b, a] == 0 and pairwise_matrix.loc[d, c] != 0:
        return True
    if pairwise_matrix.loc[d, c] == 0 and pairwise_matrix.loc[b, a] != 0:
        return False
    if pairwise_matrix.loc[b, a] == 0 and pairwise_matrix.loc[d, c] == 0:
        return pairwise_matrix.loc[a, b] > pairwise_matrix.loc[c, d]
    return (pairwise_matrix.loc[a, b] / pairwise_matrix.loc[b, a]) > (pairwise_matrix.loc[c, d] / pairwise_matrix.loc[d, c])


def compare_losses(pairwise_matrix, a, b, c, d):
    return pairwise_matrix.loc[b, a] < pairwise_matrix.loc[d, c]


methods = {'wins': compare_wins, 'losses': compare_losses, 'margins': compare_margins, 'ratios': compare_ratios}


def get_links_order(pairwise_matrix, compare_method='wins'):
    """
    Аргументы:
    pairwise_matrix - матрица попарных предпочтений, или матрица Кондорсе, Pandas DataFrame.
    compare_method - "wins", "losses", "margins", "ratios" - способ сравнения силы звеньев. 
    Если все голосующие обязаны ранжировать всех кандидатов по-разному, то четыре способа
    дают идентичный результат. 
    Возвращает матрицу попарного сравнения звеньев между всеми кандидатами, Pandas DataFrame.
    На пересечении строки с индексом (a, b) и столбца с индексом (c, d) стоит:
    1, если (a, b) - более сильное звено, чем (c, d);
    0, если звенья равны по силе;
    -1, если (c, d) - более сильное звено, чем (a, b).
    """
    if compare_method not in ("wins", "losses", "margins", "ratios"):
        raise ValueError("Invalid method name!") 
    list_of_candidates = pairwise_matrix.index.to_list()
    num_of_candidates = len(list_of_candidates)   
    squared_num = num_of_candidates**2
    links_order = pd.DataFrame(np.zeros((squared_num, squared_num)), \
    index=itertools.product(list_of_candidates, list_of_candidates), columns=itertools.product(list_of_candidates, list_of_candidates)).map(np.int64)
    for link_id in range(squared_num):
        a, b = links_order.index[link_id]
        for other_link_id in range(squared_num):
            c, d = links_order.columns[other_link_id]
            if methods[compare_method](pairwise_matrix, a, b, c, d):
            #if eval("compare_" + compare_method + "(pairwise_matrix, a, b, c, d)"):
            #if pairwise_matrix.loc[a, b] > pairwise_matrix.loc[c, d]:
                links_order.iloc[link_id, other_link_id] = 1
                links_order.iloc[other_link_id, link_id] = -1
    return links_order


def get_paths_matrix_by_links_order(links_order, list_of_candidates):
    """ 
    Аргументы:
    links_order - матрица попарного сравнения звеньев между всеми кандидатами, Pandas DataFrame.
    На пересечении строки с индексом (a, b) и столбца с индексом (c, d) стоит:
    1, если (a, b) - более сильное звено, чем (c, d);
    0, если звенья равны по силе;
    -1, если (c, d) - более сильное звено, чем (a, b).
    list_of_candidates - список фамилий (имён, индексов) кандидатов, list.
    Возвращает матрицу путей, Pandas DataFrame.
    На пересечении строки с индексом a и столбца с индексом b содержится 
    идентификатор звена, которое является критическим для сильнейшего из всех путей
    между кандидатами a и b.
    """ 
    num_of_candidates = len(list_of_candidates)
    paths_matrix = pd.DataFrame([[(0, 0) for i in range(num_of_candidates)] for j in range(num_of_candidates)], index=list_of_candidates, columns=list_of_candidates)
    for candidate_id in np.arange(num_of_candidates):
        for opponent_id in np.arange(num_of_candidates):
            paths_matrix.iat[candidate_id, opponent_id] = (list_of_candidates[candidate_id], list_of_candidates[opponent_id])
    for i in np.arange(num_of_candidates):
        for j in np.arange(num_of_candidates):
            for k in np.arange(num_of_candidates):
                if i != j and k not in (i, j):
                    if links_order.at[(paths_matrix.iat[j, i]), (paths_matrix.iat[i, k])] <= 0:
                        min_of_two = paths_matrix.iat[j, i]
                    else:
                        min_of_two = paths_matrix.iat[i, k]
                    if links_order.at[(paths_matrix.iat[j, k]), (min_of_two)] == -1:
                        paths_matrix.iat[j,k] = min_of_two
    return paths_matrix


def get_binary_relation(links_order, paths_matrix):
    """
    Аргументы:
    links_order - матрица попарного сравнения звеньев между всеми кандидатами, Pandas DataFrame.
    На пересечении строки с индексом (a, b) и столбца с индексом (c, d) стоит:
    1, если (a, b) - более сильное звено, чем (c, d);
    0, если звенья равны по силе;
    -1, если (c, d) - более сильное звено, чем (a, b).
    paths_matrix - матрица путей, Pandas DataFrame.
    На пересечении строки с индексом a и столбца с индексом b содержится 
    идентификатор звена, которое является критическим для сильнейшего из всех путей
    между кандидатами a и b.
    Возвращает список пар кандидатов, принадлежащих бинарному отношению O,
    которое выражает попарные победы кандидатов, set.
    """
    list_of_candidates = paths_matrix.index.to_list()
    num_of_candidates = len(list_of_candidates)
    binary_relation = set()
    for candidate_id in np.arange(num_of_candidates):
        for opponent_id in np.arange(num_of_candidates):
            if links_order.at[(paths_matrix.iat[candidate_id, opponent_id]), (paths_matrix.iat[opponent_id, candidate_id])] == 1:
                binary_relation.add((list_of_candidates[candidate_id], list_of_candidates[opponent_id]))
    return binary_relation


def get_winners_from_relation(binary_relation, list_of_candidates, winners_to_determine):
    """
    Аргументы:
    binary_relation - список пар кандидатов, принадлежащих бинарному отношению O,
    которое выражает попарные победы кандидатов, set.
    list_of_candidates - список фамилий (имён, индексов) кандидатов, list.
    winners_to_determine - количество определяемых победителей, int.
    Возвращает:
    result - неупорядоченный список победителей, если его возможно получить из 
    заданного бинарного отношения; иначе пустой список, list.
    full_order - список кандидатов, в отношении которых удалось установить
    занятое ими место. Словарь, ключи которого - место, а значения - фамилия (имя, метка) кандидата.
    unpicked_candidates - множество кандидатов, которых не удалось распределить по местам.
    """
    unpicked_candidates = set(list_of_candidates)
    num_of_candidates = len(list_of_candidates)
    linear_order = []
    ordered = 0
    ordered_from_end = 0
    while unpicked_candidates:
        current_possible_winners = set(unpicked_candidates)
        for candidate in unpicked_candidates:
            for opponent in unpicked_candidates:
                if candidate != opponent and (candidate, opponent) in binary_relation:
                    current_possible_winners.discard(opponent)
        if len(current_possible_winners) > 1:
           break
        new_winner = current_possible_winners.pop()
        linear_order.append(new_winner)
        ordered += 1
        unpicked_candidates.discard(new_winner)
    """
    Иногда вместо того, чтобы определять победителей, начиная с первого, 
    удаётся однозначно определить достаточное количество проигравших, 
    чтобы всех остальных можно было считать победителями.
    """
    linear_order_from_end = []
    if len(linear_order) < num_of_candidates:
        while unpicked_candidates:
            current_possible_losers = set(unpicked_candidates)
            for candidate in unpicked_candidates:
                for opponent in unpicked_candidates:
                    if candidate != opponent and (candidate, opponent) in binary_relation:
                        current_possible_losers.discard(candidate)
            if len(current_possible_losers) > 1:
                break
            
            new_loser = current_possible_losers.pop()
            linear_order_from_end.append(new_loser)
            ordered_from_end += 1
            unpicked_candidates.discard(new_loser)
    full_order = {}
    for i, winner in enumerate(linear_order):
        full_order[i + 1] = winner
    for i, loser in enumerate(reversed(linear_order_from_end)):
        full_order[i + 1 + num_of_candidates - len(linear_order_from_end)] = loser
    #print(full_order)
    if ordered >= winners_to_determine:
        result = [full_order[i + 1] for i in range(winners_to_determine)]
    elif num_of_candidates - ordered_from_end <= winners_to_determine:
        result = list(set(list_of_candidates) - {full_order[num_of_candidates - i] for i in range(num_of_candidates - winners_to_determine)})
    else:
        result = []
    return result, full_order, unpicked_candidates