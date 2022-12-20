import os
import logging
import statistics
import csv


logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logging.disable(level=logging.DEBUG)  # Uncomment this line when disabling debug print.


NAME = ['nbody', 'fannkuch-redux', 'binary-trees']
QUANTITY = ['run4', 'run8', 'run12']
ITEM = {
    'elapsed_time': 'Elapsed (wall clock) time (h:mm:ss or m:ss):',
    'max_memory': 'Maximum resident set size (kbytes):'
}
N_BENCHMARK = 50

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


if __name__ == '__main__':

    for dir_name, sub_dirs, file_names in os.walk('./crun_with_multiple_wasm'):
        sub_dirs.sort(key=lambda sub_dir: len(sub_dir))
        file_names.sort()

        logging.debug(f'Current dir is {dir_name}')

        # Extract max memory size from each .time files.
        max_memory = []
        for file_name in file_names:
            file_path = get_time_file_path(dir_name, file_name)
            memory = extract_value_from_file(file_path, ITEM['max_memory']) if file_path is not None else None
            max_memory.append(int(memory) if memory is not None else None)

        logging.debug(max_memory)
        logging.debug(f'max_memory length is {len(max_memory)}')

        # Calculate average max memory size and add it into dictionary.
        for key in max_memory_avg:
            if key in dir_name:
                avg = statistics.mean(max_memory)
                max_memory_avg[key] = avg

    print(f'max_memory_avg: {max_memory_avg}')

    # TODO: Generate 'results.csv'.
