import os
import argparse
import datetime
import pytz
from .elections_class import Elections
from .find_winners import compute_elections

dirname = os.path.dirname(os.path.abspath(__file__))
candidates_default_file = os.path.join(dirname, '..', 'candidates.csv')
ballots_default_file = os.path.join(dirname, '..', 'ballots.csv')

def list_of_ints(arg):
    return tuple(map(int, arg.split(',')))

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                    help='показать это сообщение и завершить программу')
parser.add_argument('candidates_file', nargs='?', default=candidates_default_file, type=str, help='файл со списком кандидатов, по умолчанию %(default)s')
parser.add_argument('ballots_file', nargs='?', default=ballots_default_file, type=str, help='файл со списком бюллетеней, по умолчанию %(default)s')
parser.add_argument('-y', '--years', nargs='?', const=tuple(), default=(1, 2, 3, 4, 5, 6), type=list_of_ints, help='список курсов, для которых избираются представители, по умолчанию все курсы')
parser.add_argument('-c', '--common', default=4, type=int, help='количество общих вакантных мест, по умолчанию четыре')
parser.add_argument('-r', '--report_to_file', type=str, help='файл для сохранения отчёта')
parser.add_argument('-m', '--method', choices=['wins', 'losses', 'margins', 'ratios'], default='wins', type=str, help='метод сравнения звеньев между кандидатами в матрице попарных предпочтений, по умолчанию сравнивается число побед кандидата над оппонентом')
parser.add_argument('-s', '--silent', action='store_true', default=False, help='не выводить в консоль результаты')
parser.add_argument('--store_members', type=str, help='файл для сохранения итогового списка избранных членов Студсовета')
args = parser.parse_args()

elections = Elections(cands_info=args.candidates_file, ballots_file=args.ballots_file, complete=False, years=args.years, common=args.common)
members = compute_elections(elections, compare_method=args.method, report_file=args.report_to_file, silent=args.silent)
if args.store_members is not None:
    with open(args.store_members, "a", encoding="windows-1251") as fl:
        fl.write('\n'+ str(datetime.datetime.now(pytz.timezone('Europe/Moscow'))) + '\n')
        fl.write(f"{'.\n'.join(str(i+1) + '. ' + member for i, member in enumerate(members))}.\n")
    if args.report_to_file is None:
        with open(args.report_to_file, "a", encoding="windows-1251") as fl:
            fl.write(f"Список избранных членов Студенческого совета сохранён в файл {args.store_members}")
    if not args.silent:
        print(f"Список избранных членов Студенческого совета сохранён в файл {args.store_members}")

        
