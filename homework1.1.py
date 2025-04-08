# Вариант 15. Дана целочисленная прямоугольная матрица. Определить номер первого из столбцов,
# содержащих хотя бы один нулевой элемент.
# Характеристикой строки целочисленной матрицы назовем сумму ее отрицательных четных элементов.
# Переставляя строки заданной матрицы, располагать их в соответствии с убыванием характеристик.

def task(matrix):
    cols = len(matrix[0]) if matrix else 0
    zero_col = -1
    for j in range(cols):
        for row in matrix:
            if row[j] == 0:
                zero_col = j
                break
        if zero_col != -1:
            break

    def characteristic(row):
        return sum(x for x in row if x < 0 and x % 2 == 0)

    sorted_matrix = sorted(matrix, key=characteristic, reverse=True)
    return zero_col, sorted_matrix
                #Приклад
matrix = [
    [1, 2, 0, 4],
    [-2, 3, -4, 5],
    [0, 1, 2, 3],
    [-1, -2, -3, -4]
]
zero_col, sorted_matrix = task(matrix)
print(f"Номер першого стовпця з нульовим елементом: {zero_col}")
print("Матриця після сортування:")
for row in sorted_matrix:
    print(row)