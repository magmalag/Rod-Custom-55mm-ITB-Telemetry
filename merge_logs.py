import argparse

def merge_logs(input_files, output_file):
    if not input_files:
        print("Ошибка: Нет входных файлов!")
        return

    print(f"Найдено файлов для склейки: {len(input_files)}")
    
    global_max_time = 0.0
    is_first_file = True

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filepath in input_files:
            with open(filepath, 'r', encoding='utf-8') as infile:
                lines = infile.readlines()

                # Проверяем, что файл не пустой и в нем есть данные после заголовков
                if len(lines) <= 3:
                    print(f"[-] Файл {filepath} пуст, пропускаем.")
                    continue

                # 1. Если это самый первый файл, пишем 3 строки заголовка
                if is_first_file:
                    for i in range(3):
                        outfile.write(lines[i])
                    is_first_file = False

                data_lines = lines[3:]
                
                # 2. Узнаем, с какого времени начинается текущий файл
                try:
                    first_line_parts = data_lines[0].split(',')
                    file_start_time = float(first_line_parts[0])
                except (IndexError, ValueError):
                    print(f"[-] Ошибка времени в начале файла {filepath}, пропускаем.")
                    continue

                # 3. Считаем сдвиг времени
                # Если файл первый, сдвиг = 0. 
                # Если файл второй, добавляем время конца первого файла + 0.1 секунда паузы
                if global_max_time == 0.0:
                    current_offset = 0.0
                else:
                    current_offset = global_max_time - file_start_time + 0.1

                # 4. Пишем данные с новым временем
                rows_written = 0
                for line in data_lines:
                    line = line.strip()
                    if not line: continue
                    
                    parts = line.split(',')
                    try:
                        orig_time = float(parts[0])
                        new_time = orig_time + current_offset
                        
                        # Обновляем глобальное время (чтобы следующий файл знал, где начинать)
                        if new_time > global_max_time:
                            global_max_time = new_time
                            
                        # Меняем первую колонку на новое склеенное время
                        parts[0] = f"{new_time:.3f}"
                        outfile.write(",".join(parts) + '\n')
                        rows_written += 1
                    except ValueError:
                        continue
                        
            print(f"[+] {filepath} добавлен ({rows_written} строк). Лог продлен до {global_max_time:.1f} сек.")

    print(f"\nГОТОВО! Все данные успешно склеены в файл: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Склейка нескольких очищенных логов в один")
    
    # Флаг nargs='+' позволяет передавать список файлов через пробел или маску *.log
    parser.add_argument('-i', '--input', nargs='+', required=True, help="Входные файлы (можно использовать *.log)")
    parser.add_argument('-o', '--output', required=True, help="Выходной файл (например all_data.log)")
    
    args = parser.parse_args()
    merge_logs(args.input, args.output)
