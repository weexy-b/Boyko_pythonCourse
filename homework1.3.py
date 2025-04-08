# Вариант 18
# Дaна целочисленная прямоугольная матрица. Определить:
# 1) количество строк, содержащих хотя бы один нулевой элемент;
# 2) номер столбца, в котором находится самая длинная серия одинаковых элементов

def task(matrix):
    # Количество строк с хотя бы одним нулевым элементом
    zero_rows = sum(1 for row in matrix if 0 in row)

    # Номер столбца с самой длинной серией одинаковых элементов
    if not matrix:
        return zero_rows, -1

    cols = len(matrix[0])
    max_series = -1
    result_col = -1

    for j in range(cols):
        current_series = 1
        max_current = 1
        for i in range(1, len(matrix)):
            if matrix[i][j] == matrix[i - 1][j]:
                current_series += 1
                if current_series > max_current:
                    max_current = current_series
            else:
                current_series = 1

        if max_current > max_series:
            max_series = max_current
            result_col = j

    return zero_rows, result_col


# Пример
matrix = [
    [1, 2, 3, 4],
    [0, 2, 2, 4],
    [1, 2, 2, 2],
    [1, 2, 3, 0]
]
zero_rows, series_col = task(matrix)
print(f"Кількість рядків з нульовими елементами: {zero_rows}")
print(f"Номер стовпця з найдовшою серією однакових елементів: {series_col}")