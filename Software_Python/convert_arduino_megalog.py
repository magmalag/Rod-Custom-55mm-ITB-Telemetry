import re
import argparse

def process_file(input_name, output_name):
    # Теперь всего 8 колонок: 1 время + 7 параметров
    header1 = '"DataFlash Configuration Flag","Data Buffer Length"\n'
    header2 = '8,7200\n'
    header3 = '"Elapsed Time","FRONT","REAR","DIFF","TPS","RPM","Front Map","Rear Map"\n'
    
    with open(input_name, 'r', encoding='utf-8') as infile, \
         open(output_name, 'w', encoding='utf-8') as outfile:
        
        outfile.write(header1)
        outfile.write(header2)
        outfile.write(header3)
        
        start_time = None
        
        for line in infile:
            # 1. Берем время
            time_match = re.search(r'\[(\d{2}):(\d{2}):(\d{2}\.\d{3})\]', line)
            if not time_match: continue
            
            h, m, s = map(float, [time_match.group(1), time_match.group(2), time_match.group(3)])
            current_time = (h * 3600) + (m * 60) + s
            if start_time is None: start_time = current_time
            elapsed_time = current_time - start_time
            
            # 2. Чистим строку
            clean_line = re.sub(r'\[.*?\]', '', line)
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", clean_line)
            
            # 3. Фильтр: нам нужно 8 чисел (1 лишнее + 7 наших параметров)
            if len(nums) == 8:
                # Берем nums[1] по nums[7], пропуская nums[0] (то самое лишнее число)
                data = nums[1:8] 
                row = ["{:.3f}".format(elapsed_time)] + data
                outfile.write(",".join(row) + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', required=True)
    parser.add_argument('-o', required=True)
    args = parser.parse_args()
    process_file(args.i, args.o)
