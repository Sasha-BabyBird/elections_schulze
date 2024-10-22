## Реализация подсчета голосов на выборах в Студенческий совет ПМ-ПУ методом Шульце вместо использовавшегося ранее метода максимина (Симпсона).
Для работы необходимы два `csv`-файла: список кандидатов и бюллетеней. В таблице кандидатов названия столбцов могут быть произвольными, но первая строка не должна содержать данные. В таблице бюллетеней каждый столбец должен называться в соответствии с именем (фамилией, идентификатором) соответствующего кандидата.
# Использование из командной строки:
`python -m sspmpu_elections [options]`

Неименованные (позиционные) аргументы:
1. Список кандидатов (по умолчанию `candidates.csv`).
2. Список бюллетеней (по умолчанию `ballots.csv`).

`-y`, `--years`: список курсов, для которых избираются представители, по умолчанию все курсы;

`-c`, `--common`: количество общих вакантных мест, по умолчанию четыре;

`-r`, `--report_to_file`: файл для сохранения отчета;

`-m`, `--method`: метод сравнения звеньев между кандидатами в матрице попарных предпочтений, по умолчанию сравнивается число побед кандидата над оппонентом (`'wins'`). Варианты: `'wins'`, `'losses'`, `'margins'`, `'ratios'`;

`-s`, `--silent`: не выводить в консоль результаты;

`--store_members`: файл для сохранения итогового списка избранных членов Студенческого совета ПМ-ПУ.

# Использование в качестве модуля
Файл `manual.py` в корневой папке.

Источник: *The Schulze Method of Voting / M. Schulze / arXiv:1804.02973v14*

