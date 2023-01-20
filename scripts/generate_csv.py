import os
import logging
import statistics
import csv
import pprint


# Log settings.
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logging.disable(level=logging.DEBUG)  # Comment this line when enabling debug print.


NAME = ['nbody', 'fannkuch-redux', 'binary-trees']
QUANTITY = ['run1', 'run2', 'run3', 'run4', 'run8', 'run12']
N_BENCHMARK = 50
ITEM = {
    'elapsed_time': 'app execution time:',
    'start_time': 'app start time:',
    'end_time': 'app end time:',
    'init_time': 'container init time:',
    'command_start_time': 'crun start time:',
    'max_memory': 'Maximum resident set size (kbytes):'
}

results = {
    'single_wasm': {},
    'multiple_wasm': {}
}
max_memory_avg = {name + '/' + quantity: 0 for name in NAME for quantity in QUANTITY}
elapsed_time_avg = {name + '/' + quantity: 0 for name in NAME for quantity in QUANTITY}
startup_time_avg = {name + '/' + quantity: 0 for name in NAME for quantity in QUANTITY}

logging.debug(max_memory_avg)
logging.debug(elapsed_time_avg)
logging.debug(startup_time_avg)


def get_file_path(dir_name: str, file_name: str) -> str:
    tmp_dir_name = dir_name.split('/')[-2] + '/' + dir_name.split('/')[-1]
    for name in NAME:
        for quantity in QUANTITY:
            if f'{name}/{quantity}' == tmp_dir_name:
                file_path = f'{dir_name}/{file_name}'
                return file_path


def extract_value_from_file(file_path: str, item: str) -> str:
    with open(file_path) as file:
        for line in file:
            if item in line:
                value = line[len(item) + 1:].strip()
                logging.debug(f'{file_path}: {item} {value}')
                return value


def extract_values_from_file(file_path: str, item: str) -> list:
    with open(file_path) as file:
        values = []
        for line in file:
            if item in line:
                values.append(line[len(item) + 1:].strip())

        logging.debug(f'{file_path}: {item} {values}')
        return values


def extract_quantity_from_dir_name(dir_name: str) -> int:
    dir_name = dir_name.split('/')[-1]
    if ('run1' == dir_name) or ('run2' == dir_name) or ('run3' == dir_name) or ('run4' == dir_name) or ('run8' == dir_name) or ('run12' == dir_name):
        index = dir_name.rfind('run') + len('run')
        quantity = int(dir_name[index:])
        return quantity

    return -1


# time1 - time2
def unixtime_sub(time1: str, time2: str) -> float:
    unix_time1 = int(float(time1) * (10 ** 6))
    unix_time2 = int(float(time2) * (10 ** 6))
    result = (unix_time1 - unix_time2) / (10 ** 3) # msec
    return result


def calc_elapsed_time(file_path: str) -> float:
    start_times = extract_values_from_file(file_path, ITEM['start_time'])
    end_times = extract_values_from_file(file_path, ITEM['end_time'])

    min_start_time = min(start_times)
    max_end_time = max(end_times)

    return unixtime_sub(max_end_time, min_start_time) / (10 ** 3) # msec to sec


def calc_cmd_overhead_time(file_path: str, quantity: int) -> float:
    cmd_start_times = extract_values_from_file(file_path, ITEM['command_start_time'])
    init_times = extract_values_from_file(file_path, ITEM['init_time'])

    min_cmd_start_time = min(cmd_start_times)
    min_init_time = min(init_times)

    # Calculate command overhead time.
    cmd_overhead_time = unixtime_sub(min_init_time, min_cmd_start_time) * quantity
    logging.debug(f'{file_path}: cmd_overhead = {cmd_overhead_time} ms')

    return cmd_overhead_time


def calc_startup_time(file_path: str, mode: str, quantity: int) -> float:
    init_times = extract_values_from_file(file_path, ITEM['init_time'])
    start_times = extract_values_from_file(file_path, ITEM['start_time'])

    min_init_time = min(init_times)
    max_start_time = max(start_times)

    startup_time = unixtime_sub(max_start_time, min_init_time)

    if mode == 'crun':
        cmd_overhead_time = calc_cmd_overhead_time(file_path, quantity)

        # Calculate startup time without command overhead.
        startup_time = startup_time - cmd_overhead_time

    return startup_time


def generate_wasm_result(mode: str) -> None:
    for dir_name, sub_dirs, file_names in os.walk(f'./{mode}'):
        sub_dirs.sort(key=lambda sub_dir: len(sub_dir))
        file_names.sort()

        logging.debug(f'Current dir is {dir_name}')

        if extract_quantity_from_dir_name(dir_name) == -1:
            continue

        quantity = extract_quantity_from_dir_name(dir_name)
        max_memories = []
        elapsed_times = []
        startup_times = []
        for file_name in file_names:
            _, ext = os.path.splitext(file_name)
            file_path = get_file_path(dir_name, file_name)
            if ext != '.time':
                tmp_elapsed_time = calc_elapsed_time(file_path)
                tmp_startup_time = calc_startup_time(file_path, mode, quantity)
                elapsed_times.append(tmp_elapsed_time)
                startup_times.append(tmp_startup_time)
            else:
                tmp_memory = extract_value_from_file(file_path, ITEM['max_memory'])
                max_memories.append(int(tmp_memory))

        logging.debug(max_memories)
        logging.debug(f'max_memories length is {len(max_memories)}')
        logging.debug(elapsed_times)
        logging.debug(f'elapsed_times length is {len(elapsed_times)}')
        logging.debug(startup_times)
        logging.debug(f'startup_times length is {len(startup_times)}')

        # Add average max memory into dictionary.
        for key in max_memory_avg:
            if key == dir_name.split('/')[-2] + '/' + dir_name.split('/')[-1]:
                if mode == 'crun':
                    max_memory_avg[key] = statistics.mean(max_memories) * quantity
                elif mode == 'crun_with_multiple_wasm':
                    max_memory_avg[key] = statistics.mean(max_memories)

        # Add average elapsed time into dictionary.
        for key in elapsed_time_avg:
            if key == dir_name.split('/')[-2] + '/' + dir_name.split('/')[-1]:
                elapsed_time_avg[key] = statistics.mean(elapsed_times)

        # Add average startup time into dictionary.
        for key in startup_time_avg:
            if key == dir_name.split('/')[-2] + '/' + dir_name.split('/')[-1]:
                startup_time_avg[key] = statistics.mean(startup_times)

    logging.debug(f'max_memory_avg: {max_memory_avg}')
    logging.debug(f'elapsed_time_avg: {elapsed_time_avg}')
    logging.debug(f'startup_time_avg: {startup_time_avg}')

    if mode == 'crun':
        results['single_wasm']['max_memory_avg'] = max_memory_avg.copy()
        results['single_wasm']['elapsed_time_avg'] = elapsed_time_avg.copy()
        results['single_wasm']['startup_time_avg'] = startup_time_avg.copy()
    elif mode == 'crun_with_multiple_wasm':
        results['multiple_wasm']['max_memory_avg'] = max_memory_avg.copy()
        results['multiple_wasm']['elapsed_time_avg'] = elapsed_time_avg.copy()
        results['multiple_wasm']['startup_time_avg'] = startup_time_avg.copy()


def generate_csv(name: str, item: str) -> None:
    with open(f'./{name}', 'w') as csv_file:
        writer = csv.writer(csv_file)

        # Write the header
        header = [name + '/' + quantity for name in NAME for quantity in QUANTITY]
        writer.writerow(header)

        # Write the data
        single_wasm = results['single_wasm'][item]
        multiple_wasm = results['multiple_wasm'][item]
        data = [[] for i in range(2)]
        for key in header:
            data[0].append(single_wasm[key])
            data[1].append(multiple_wasm[key])
        writer.writerow(data[0])
        writer.writerow(data[1])


if __name__ == '__main__':
    generate_wasm_result('crun')
    generate_wasm_result('crun_with_multiple_wasm')

    pprint.pprint(results)

    # Generate csv files.
    generate_csv('max_memory_avg.csv', 'max_memory_avg')
    generate_csv('elapsed_time_avg.csv', 'elapsed_time_avg')
    generate_csv('startup_time_avg.csv', 'startup_time_avg')
