import os
import argparse
import datetime
try:
    from zoneinfo import ZoneInfo
    def _now():
        return datetime.datetime.now(ZoneInfo('Europe/Moscow'))
except Exception:                                   # pragma: no cover
    def _now():
        return datetime.datetime.now()

from .elections_class import Elections
from .find_winners import compute_elections, REPORT_ENCODING

dirname = os.path.dirname(os.path.abspath(__file__))
candidates_default_file = os.path.join(dirname, '..', 'candidates.csv')
ballots_default_file = os.path.join(dirname, '..', 'ballots.csv')


def list_of_ints(arg):
    try:
        years = tuple(int(x) for x in arg.split(','))
    except ValueError:
        raise argparse.ArgumentTypeError("курсы должны быть целыми числами через запятую, напр. 1,2,5")
    bad = [y for y in years if y not in (1, 2, 3, 4, 5, 6)]
    if bad:
        raise argparse.ArgumentTypeError(f"недопустимые курсы {bad}; допустимы 1..6")
    return years


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                    help='показать это сообщение и завершить программу')
parser.add_argument('candidates_file', nargs='?', default=candidates_default_file, type=str,
                    help='файл со списком кандидатов, по умолчанию %(default)s')
parser.add_argument('ballots_file', nargs='?', default=ballots_default_file, type=str,
                    help='файл со списком бюллетеней, по умолчанию %(default)s')
parser.add_argument('-y', '--years', nargs='?', const=tuple(), default=(1, 2, 3, 4, 5, 6),
                    type=list_of_ints, help='курсы, для которых избираются представители, по умолчанию все')
parser.add_argument('-c', '--common', default=4, type=int, help='число общих вакантных мест, по умолчанию 4')
parser.add_argument('-r', '--report_to_file', type=str, help='файл для сохранения отчёта')
parser.add_argument('-m', '--method', choices=['wins', 'losses', 'margins', 'ratios'], default='wins',
                    type=str, help='мера силы звена; по умолчанию winning votes (wins)')
parser.add_argument('--seed', type=int, default=0,
                    help='зерно для разрешения ничьих (зафиксируйте публично до подсчёта), по умолчанию 0')
parser.add_argument('--strict', action='store_true', default=False,
                    help='требовать строгие полные ранжирования (отклонять равные приоритеты и пропуски)')
parser.add_argument('-s', '--silent', action='store_true', default=False, help='не выводить в консоль')
parser.add_argument('--store_members', type=str, help='файл для сохранения списка избранных членов')
args = parser.parse_args()

elections = Elections(cands_info=args.candidates_file, ballots_file=args.ballots_file,
                      complete=False, years=args.years, common=args.common, require_strict=args.strict)
members = compute_elections(elections, compare_method=args.method,
                            report_file=args.report_to_file, silent=args.silent, seed=args.seed)

if members is not None and args.store_members is not None:
    dot_nl = '.\n'
    with open(args.store_members, "a", encoding=REPORT_ENCODING) as fl:
        fl.write('\n' + str(_now()) + '\n')
        fl.write(dot_nl.join(f"{i + 1}. {m}" for i, m in enumerate(members)) + ".\n")
    note = f"Список избранных членов Студсовета сохранён в файл {args.store_members}"
    if args.report_to_file is not None:                # БЫЛО: if ... is None -> open(None) (краш)
        with open(args.report_to_file, "a", encoding=REPORT_ENCODING) as fl:
            fl.write('\n' + note)
    if not args.silent:
        print(note)
