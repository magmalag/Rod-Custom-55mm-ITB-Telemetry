import csv
import argparse

# Твои оси X (Обороты) и Y (Дроссель)
RPM_BINS = [1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500]
TPS_BINS = [0.0, 2.5, 5.0, 7.5, 10.0, 15.0, 22.5, 35.0, 50.0, 70.0, 100.0]

def get_nearest(value, bins):
    return min(bins, key=lambda x: abs(x - value))

def build_map(input_log, output_csv):
    # Создаем пустую таблицу
    table_data = {(tps, rpm): [] for tps in TPS_BINS for rpm in RPM_BINS}

    print(f"Читаем лог: {input_log}...")
    
    with open(input_log, 'r', encoding='utf-8') as f:
        # Пропускаем 3 строки заголовков
        for _ in range(3):
            next(f, None)
            
        for line in f:
            parts = line.strip().split(',')
            
            # Проверяем, что в строке хватает данных (должно быть 8 колонок параметров + время = 9 колонок)
            if len(parts) >= 8:
                try:
                    # Индексы согласно структуре твоего очищенного лога:
                    tps = float(parts[4])
                    rpm = float(parts[5])
                    front_map = float(parts[6])
                    rear_map = float(parts[7])
                    
                    # Считаем разницу Front Map - Rear Map
                    map_diff = front_map - rear_map
                    
                    nearest_tps = get_nearest(tps, TPS_BINS)
                    nearest_rpm = get_nearest(rpm, RPM_BINS)
                    
                    # Записываем РАЗНИЦУ в эту ячейку
                    table_data[(nearest_tps, nearest_rpm)].append(map_diff)
                except ValueError:
                    continue

    print(f"Генерируем таблицу (Front Map - Rear Map): {output_csv}...")
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Шапка таблицы (Обороты)
        header = ["TPS \\ RPM"] + RPM_BINS
        writer.writerow(header)
        
        # Строки таблицы (Дроссель от 100% к 0%)
        for tps in reversed(TPS_BINS):
            row = [tps]
            for rpm in RPM_BINS:
                values = table_data[(tps, rpm)]
                if values:
                    # Считаем среднее значение разницы MAPов для этой ячейки
                    avg_val = sum(values) / len(values)
                    row.append(f"{avg_val:.2f}")
                else:
                    # Оставляем пустой, если данных не было
                    row.append("") 
            writer.writerow(row)
            
    print("Готово! Открывай файл в Excel.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # На вход даем ОЧИЩЕННЫЙ лог
    parser.add_argument('-i', required=True, help="Входной чистый .log файл")
    parser.add_argument('-o', required=True, help="Выходной файл таблицы (например map_diff.csv)")
    args = parser.parse_args()
    build_map(args.i, args.o)
