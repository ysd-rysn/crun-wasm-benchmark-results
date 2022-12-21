import os
import logging
import statistics
import csv
import pprint


# Log settings.
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logging.disable(level=logging.DEBUG)  # Comment this line when enabling debug print.


NAME = ['nbody', 'fannkuch-redux', 'binary-trees']
QUANTITY = ['run4', 'run8', 'run12']
N_BENCHMARK = 50
ITEM = {
    'elapsed_time': 'Elapsed (wall clock) time (h:mm:ss or m:ss):',
    'max_memory': 'Maximum resident set size (kbytes):'
}

results = {
    'single_wasm': {},
    'multiple_wasm': {}
}
max_memory_avg = {name + '/' + quantity: 0 for name in NAME for quantity in QUANTITY}
elapsed_time_avg = {name + '/' + quantity: '0:0' for name in NAME for quantity in QUANTITY}

logging.debug(max_memory_avg)
logging.debug(elapsed_time_avg)


def get_time_file_path(dir_name: str, file_name: str) -> str:
    for name in NAME:
        for quantity in QUANTITY:
            if f'{name}/{quantity}' in dir_name:
                file_path = f'{dir_name}/{file_name}'
                return file_path


def extract_value_from_file(file_path: str, item: str) -> int:
    with open(file_path) as file:
        for line in file:
            if item in line:
                value = line[len(item) + 1:].strip()
                logging.debug(f'{file_path}: {item} {value}')
                return value


def extract_quantity_from_dir_name(dir_name: str) -> int:
    if ('run4' in dir_name) or ('run8' in dir_name) or ('run12' in dir_name):
        index = dir_name.rfind('run') + len('run')
        quantity = int(dir_name[index:])
        return quantity
    
    return -1


def generate_single_wasm_result() -> None:
    for dir_name, sub_dirs, file_names in os.walk('./crun'):
        sub_dirs.sort(key=lambda sub_dir: len(sub_dir))
        file_names.sort()

        logging.debug(f'Current dir is {dir_name}')

        if extract_quantity_from_dir_name(dir_name) == -1:
            continue

        # Extract max memory size from each .time files.
        quantity = extract_quantity_from_dir_name(dir_name)
        max_memories = [[] for i in range(quantity)]
        i = 0
        for file_name in file_names:
            file_path = get_time_file_path(dir_name, file_name)
            memory = extract_value_from_file(file_path, ITEM['max_memory'])
            index = i // N_BENCHMARK 
            max_memories[index].append(int(memory))
            i += 1

        logging.debug(max_memories)
        logging.debug(f'max_memories length is {len(max_memories)}')

        # Calculate average max memory size.
        each_avg = []
        avg = 0
        for max_memory in max_memories:
            each_avg.append(statistics.mean(max_memory))
        for value in each_avg:
            avg += value

        # Add avg into dictionary.
        for key in max_memory_avg:
            if key in dir_name:
                max_memory_avg[key] = avg

    logging.debug(f'max_memory_avg: {max_memory_avg}')

    results['single_wasm']['max_memory_avg'] = max_memory_avg.copy()
    results['single_wasm']['elapsed_time_avg'] = elapsed_time_avg.copy()


def generate_multiple_wasm_result() -> None:
    for dir_name, sub_dirs, file_names in os.walk('./crun_with_multiple_wasm'):
        sub_dirs.sort(key=lambda sub_dir: len(sub_dir))
        file_names.sort()

        logging.debug(f'Current dir is {dir_name}')

        if extract_quantity_from_dir_name(dir_name) == -1:
            continue

        # Extract max memory size from each .time files.
        max_memory = []
        for file_name in file_names:
            file_path = get_time_file_path(dir_name, file_name)
            memory = extract_value_from_file(file_path, ITEM['max_memory'])
            max_memory.append(int(memory))

        logging.debug(max_memory)
        logging.debug(f'max_memory length is {len(max_memory)}')

        # Calculate average max memory size and add it into dictionary.
        for key in max_memory_avg:
            if key in dir_name:
                avg = statistics.mean(max_memory)
                max_memory_avg[key] = avg

    logging.debug(f'max_memory_avg: {max_memory_avg}')

    results['multiple_wasm']['max_memory_avg'] = max_memory_avg.copy()
    results['multiple_wasm']['elapsed_time_avg'] = elapsed_time_avg.copy()


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
    generate_single_wasm_result()
    generate_multiple_wasm_result()

    pprint.pprint(results)

    # Generate csv files.
    generate_csv('max_memory_avg.csv', 'max_memory_avg')