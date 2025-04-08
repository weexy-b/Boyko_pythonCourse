#Вариант 16
# Упорядочить строки целочисленной прямоугольной матрицы по возрастанию количества
# одинаковых элементов в каждой строке.
# Найти номер первого из столбцов, не содержащих ни одного отрицательного элемента

def task(matrix):
    # Упорядочиваем строки по возрастанию количества одинаковых элементов
    def count_duplicates(row):
        from collections import Counter
        counts = Counter(row)
        return sum(v for v in counts.values() if v > 1)

    sorted_matrix = sorted(matrix, key=count_duplicates)

    # Первый столбец без отрицательных элементов
    cols = len(matrix[0]) if matrix else 0
    positive_col = -1
    for j in range(cols):
        has_negative = False
        for row in matrix:
            if row[j] < 0:
                has_negative = True
                break
        if not has_negative:
            positive_col = j
            break

    return sorted_matrix, positive_col


    # Пример
matrix = [
    [-1, 2, 2, 4],
    [1, 1, -1, 1],
    [2, 3, 4, 5],
    [1, -2, 3, 3]
]
sorted_matrix, positive_col = task(matrix)
print("Матриця після сортування:")
for row in sorted_matrix:
    print(row)
print(f"Номер першого стовпця без від'ємних елементів: {positive_col}")