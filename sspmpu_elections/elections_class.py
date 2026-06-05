from functools import cached_property
from .schulze_utils import np, pd


class Elections():
    """
    Профиль выборов: бюллетени, кандидаты и сведения о вакантных местах.
    complete=True — полные перевыборы; иначе задаются курсы (years) и число общих мест (common).
    """
    def __init__(self, cands_info, ballots_file, complete=True,
                 years=(1, 2, 3, 4, 5, 6), common=4, require_strict=False):
        self.candidates = pd.read_csv(cands_info, delimiter=';', index_col='№',
                                      skipinitialspace=True, on_bad_lines='skip')
        self.candidates.sort_index(inplace=True)
        self.ballots = pd.read_csv(ballots_file, delimiter=';', index_col='№',
                                   skipinitialspace=True, on_bad_lines='skip')
        self.ballots.sort_index(inplace=True)
        self.num_of_ballots = self.ballots.shape[0]
        self.num_of_candidates = self.candidates.shape[0]

        names = self.candidates.iloc[:, 0].to_list()
        # --- защита: фамилия используется как идентификатор кандидата ---
        dups = [n for n in set(names) if names.count(n) > 1]
        if dups:
            raise ValueError(
                "Повторяющиеся идентификаторы кандидатов (столбец имён): "
                f"{sorted(dups)}. Сделайте идентификаторы уникальными "
                "(например, добавьте инициалы или используйте № как ключ "
                "и в candidates.csv, и в ballots.csv).")
        missing = set(self.ballots.columns) ^ set(names)
        if missing:
            raise ValueError(
                "Столбцы бюллетеней не совпадают со списком кандидатов. "
                f"Различия: {sorted(missing)}.")

        cols = sorted(self.ballots.columns.to_list(),
                      key=lambda x, cands=self.candidates:
                      cands[cands.iloc[:, 0] == x].index.to_list()[0])
        self.ballots_matrix = self.ballots.reindex(columns=cols)
        # Строгая проверка (полные строгие ранжирования) — ПО ЗАПРОСУ. Базовое поведение,
        # как и раньше, допускает равные приоритеты и пропуски (трактуются как «несравнимо»).
        if require_strict:
            self._validate_ballots()

        if complete:
            self.years = (1, 2, 3, 4, 5, 6)
            self.common = 4
        else:
            if isinstance(years, (float, int)):
                years = [years]
            self.years = tuple(sorted(years))
            self.common = common

    def _validate_ballots(self):
        """Каждый бюллетень должен быть строгим полным ранжированием (перестановкой)."""
        C = self.num_of_candidates
        for bid, row in self.ballots_matrix.iterrows():
            vals = row.to_numpy()
            if np.isnan(vals).any():
                raise ValueError(
                    f"Бюллетень №{bid} неполный (есть пропуски). Требуется строгое "
                    "полное ранжирование всех кандидатов.")
            if len(set(vals.tolist())) != C:
                raise ValueError(
                    f"Бюллетень №{bid} содержит одинаковые приоритеты у разных кандидатов. "
                    "Требуется строгое (без равенств) ранжирование.")

    @cached_property
    def pairwise_matrix(self):
        """Матрица попарных предпочтений (матрица Кондорсе). Кэшируется."""
        ranks = self.ballots_matrix.to_numpy(dtype=float)            # float: терпит равные ранги и пропуски
        C = self.num_of_candidates
        pm = np.zeros((C, C), dtype=np.int64)
        for i in range(C):
            for j in range(i + 1, C):
                gi = int(np.sum(ranks[:, i] < ranks[:, j]))          # i предпочтён j
                gj = int(np.sum(ranks[:, j] < ranks[:, i]))
                pm[i, j] = gi
                pm[j, i] = gj
        names = self.candidates.iloc[:, 0].to_list()
        return pd.DataFrame(pm, index=names, columns=names)

    @cached_property
    def pairwise_matrices_by_years(self):
        """Словарь матриц попарных предпочтений по каждому курсу (использует кэш)."""
        yearsdict = {}
        for year in self.years:
            valid = self.candidates[self.candidates.iloc[:, 1] == year].iloc[:, 0].to_list()
            yearsdict[year] = (pd.DataFrame() if not valid
                               else self.pairwise_matrix.loc[valid, valid])
        return yearsdict
