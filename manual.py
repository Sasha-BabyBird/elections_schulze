from sspmpu_elections import determine_winners, compute_elections, Elections


elections = Elections("examples/candidates.csv", "examples/ballots.csv", complete=False, years=[1, 5], common=3)
#print(elections.pairwise_matrices_by_years)
#print(elections.candidates[elections.candidates.iloc[:, 0]=='Богданова'].index.to_list()[0])
#print(elections.ballots.columns.to_list())
#print(elections.ballots_matrix)

'''
pairwise_matrix = np.array([[0, 5, 5, 3],
                            [4, 0, 7, 5],
                            [4, 2, 0, 5],
                            [6, 4, 4, 0]])
'''
elections_ex_13 = Elections("examples/candidates_ex13.csv", "examples/ballots_ex13.csv", complete=False, years=[1], common=2)
elections_ex_6 = Elections("examples/candidates_ex6.csv", "examples/ballots_ex6.csv", complete=False, years=[1], common=2)
elections_ex_4 = Elections("examples/candidates_ex4.csv", "examples/ballots_ex4.csv", complete=False, years=[1], common=2)
elections_ex_11 = Elections("examples/candidates_ex11.csv", "examples/ballots_ex11.csv", complete=False, years=[1], common=1)
elections_ex_5 = Elections("examples/candidates_ex5.csv", "examples/ballots_ex5.csv", complete=False, years=[1], common=2)
elections_ex_12 = Elections("examples/candidates_ex12.csv", "examples/ballots_ex12.csv", complete=False, years=[], common=2)
#pairwise_matrix_book_13 = pd.DataFrame(np.array([[0,3,2], [2,0,4], [3,1,0]]), index=['a', 'b', 'c'], columns=['a', 'b', 'c'])
for i in range(7):
    print(f'ПОБЕДИТЕЛИ В ПРИМЕРЕ С ВЫБОРОВ-2023: {determine_winners(elections.ballots_matrix, elections.pairwise_matrix, i+1)}\n')

for i in range(4):
    print(f'ПОБЕДИТЕЛИ В ПРИМЕРЕ №4 (НИЧЬЯ И СЛУЧАЙНЫЙ ВЫБОР): {determine_winners(elections_ex_4.ballots_matrix, elections_ex_4.pairwise_matrix, i+1)}\n')

for i in range(4):
    print(f'ПОБЕДИТЕЛИ В ПРИМЕРЕ №6 (НИЧЬЯ И СЛУЧАЙНЫЙ ВЫБОР): {determine_winners(elections_ex_6.ballots_matrix, elections_ex_6.pairwise_matrix, i+1)}\n')

for i in range(3):
    print(f'ПОБЕДИТЕЛИ В ПРИМЕРЕ №13 (НИЧЬЯ И СЛУЧАЙНЫЙ ВЫБОР): {determine_winners(elections_ex_13.ballots_matrix, elections_ex_13.pairwise_matrix, i+1)}\n')


#СПИСОК ДОЛЖЕН СОДЕРЖАТЬ "a", НО НЕ ДОЛЖЕН СОДЕРЖАТЬ "b"
print(f'ПОБЕДИТЕЛИ В ПРИМЕРЕ №5 (НИЧЬЯ С ЗАПРЕТОМ ЗВЕНЬЕВ): {determine_winners(elections_ex_5.ballots_matrix, elections_ex_5.pairwise_matrix, 2)}\n')

#СПИСОК ДОЛЖЕН СОДЕРЖАТЬ "a", НО НЕ ДОЛЖЕН СОДЕРЖАТЬ "c"
print(f'ПОБЕДИТЕЛИ В ПРИМЕРЕ №11 (НИЧЬЯ С ЗАПРЕТОМ ЗВЕНЬЕВ): {determine_winners(elections_ex_11.ballots_matrix, elections_ex_11.pairwise_matrix, 3)}\n')

#СПИСОК ДОЛЖЕН СОДЕРЖАТЬ "a", НО НЕ ДОЛЖЕН СОДЕРЖАТЬ "c"
print(f'ПОБЕДИТЕЛИ В ПРИМЕРЕ №12 (НИЧЬЯ С ЗАПРЕТОМ ЗВЕНЬЕВ): {determine_winners(elections_ex_12.ballots_matrix, elections_ex_12.pairwise_matrix, 2)}\n')
#print(basic_schulze(elections))
print(compute_elections(elections))
print(compute_elections(elections_ex_12))













