from .schulze_utils import np, pd

class Elections():
    """
    Класс для работы с профилями выборов. Профиль - это совокупность бюллетеней, кандидатов,
    а также информация о местах, в конкурсе на которые участвуют кандидаты.
    Можно задать либо complete=True, и тогда класс реализует полные перевыборы,
    либо вручную указать список курсов, места представителей которых должны быть заполнены,
    а также количество общих вакантных мест.
    """
    def __init__(self, cands_info, ballots_file, complete=True, years=(1, 2, 3, 4, 5, 6), common=4):
        #print(cands_info)
        self.candidates = pd.read_csv(cands_info, delimiter=';', index_col='№', skipinitialspace=True, on_bad_lines='skip')
        self.candidates.sort_index(inplace=True)
        self.ballots = pd.read_csv(ballots_file, delimiter=';', index_col='№', skipinitialspace=True, on_bad_lines='skip')
        self.ballots.sort_index(inplace=True)
        self.num_of_ballots = self.ballots.shape[0]
        self.num_of_candidates = self.candidates.shape[0]
        cols = sorted(self.ballots.columns.to_list(), key=lambda x, cands=self.candidates: cands[cands.iloc[:, 0] == x].index.to_list()[0])
        self.ballots_matrix = self.ballots.reindex(columns=cols)
        if complete:
            self.years = (1, 2, 3, 4, 5, 6)
            self.common = 4
        else:
            if isinstance(years, (float, int)):
                years = [years]
            self.years = tuple(sorted(years))
            self.common = common

    @property
    def pairwise_matrix(self):
        """
        Матрица попарных предпочтений, также известная как
        матрица Кондорсе.
        Вычисляемое свойство.
        Работает и в ситуации, когда голосующим разрешается ранжировать
        не всех кандидатов и ставить одинаковые приоритеты.
        """
        pairwise_matrix = np.zeros((self.num_of_candidates, self.num_of_candidates))
        for ballot_id in np.arange(self.num_of_ballots):
            for candidate_id in np.arange(self.num_of_candidates-1):
                for opponent_id in np.arange(candidate_id + 1, self.num_of_candidates):
                    if self.ballots_matrix.iat[ballot_id, candidate_id] > self.ballots_matrix.iat[ballot_id, opponent_id]:
                        pairwise_matrix[opponent_id, candidate_id] += 1
                    elif self.ballots_matrix.iat[ballot_id, candidate_id] < self.ballots_matrix.iat[ballot_id, opponent_id]:
                        pairwise_matrix[candidate_id, opponent_id] += 1

        return pd.DataFrame(pairwise_matrix, index=self.candidates.iloc[:, 0].to_list(), columns=self.candidates.iloc[:, 0].to_list()).map(np.int64)

    @property
    def pairwise_matrices_by_years(self):
        """
        Список (словарь) матриц попарных предпочтений, соответствующих конкурсу
        на каждое из мест представителей курсов.
        Вычисляемое свойство.
        """
        yearsdict = {}
        for year in self.years:
            valid_cands = self.candidates[self.candidates.iloc[:, 1] == year].iloc[:, 0].to_list()
            if not valid_cands:
                yearsdict[year] = pd.DataFrame()
            else:
                yearsdict[year] = self.pairwise_matrix.loc[valid_cands, valid_cands]
        return yearsdict