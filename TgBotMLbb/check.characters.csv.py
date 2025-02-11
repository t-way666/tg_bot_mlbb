import csv

def check_csv(filename):
    with open(filename, 'r', encoding='utf-8') as file:  # Указываем кодировку UTF-8
        reader = csv.reader(file)
        header = next(reader)  # Считываем заголовок
        expected_fields = len(header)  # Количество ожидаемых полей
        for i, row in enumerate(reader, 2):  # Начинаем с 2, так как 1 - заголовок
            num_fields = len(row)
            if num_fields != expected_fields:
                print(f"Ошибка в строке {i}: Ожидалось {expected_fields} полей, найдено {num_fields}")

check_csv('characters.csv')