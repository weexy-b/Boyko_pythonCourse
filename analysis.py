import argparse
import csv
import datetime
import logging
import os
import shutil
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import requests


def setup_logger(log_level=logging.INFO):
    # Set up file logger with the specified log level
    logger = logging.getLogger('user_data_processor')
    logger.setLevel(log_level)

    # Create file handler
    file_handler = logging.FileHandler('user_data_processing.log')
    file_handler.setLevel(log_level)

    # Create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(file_handler)

    return logger


def download_user_data(num_users=5000, filename='output.csv'):
    # Download user data from randomuser.me API
    logger = logging.getLogger('user_data_processor')
    logger.info(f"Завантаження {num_users} записів користувачів від randomuser.me")

    try:
        response = requests.get(
            f'https://randomuser.me/api/?results={num_users}&format=csv&inc=gender,name,location,email,login,dob,registered,phone,cell,id,picture,nat'
        )
        response.raise_for_status()

        with open(filename, 'wb') as f:
            f.write(response.content)

        logger.info(f"Дані успішно завантажено в {filename}")
        return filename
    except Exception as e:
        logger.error(f"Не вдалося завантажити дані користувача: {str(e)}")
        raise


def process_name_title(title):
    # Process name.title according to specified rules
    title_mapping = {
        'Mrs': 'missis',
        'Ms': 'miss',
        'Mr': 'mister',
        'Madame': 'mademoiselle'
    }
    return title_mapping.get(title, title)


def process_dob_date(dob_str):
    # Convert date to month/day/year format.
    try:
        dt = datetime.datetime.strptime(dob_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        return dt.strftime('%m/%d/%Y')
    except:
        return dob_str


def process_register_date(reg_str):
    # Convert register.date to month-day-year, hours:minutes:second format
    try:
        dt = datetime.datetime.strptime(reg_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        return dt.strftime('%m-%d-%Y, %H:%M:%S')
    except:
        return reg_str


def calculate_current_time(timezone_offset):
    # Calculate current time based on timezone offset.
    utc_now = datetime.datetime.utcnow()
    offset = datetime.timedelta(hours=int(timezone_offset.split(':')[0]),
                                minutes=int(timezone_offset.split(':')[1]))
    local_time = utc_now + offset
    return local_time.strftime('%Y-%m-%d %H:%M:%S')


def process_csv(input_file, output_file, gender_filter=None, row_limit=None):
    # Process the CSV file according to requirements
    logger = logging.getLogger('user_data_processor')
    logger.info(f"Обробка файлу CSV: {input_file}")

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
                open(output_file, 'w', encoding='utf-8', newline='') as outfile:

            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames + ['global_index', 'current_time']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            row_count = 0
            for idx, row in enumerate(reader, 1):
                # Apply filters if specified
                if gender_filter and row['gender'].lower() != gender_filter.lower():
                    continue

                # Process fields
                row['name.title'] = process_name_title(row['name.title'])
                row['dob.date'] = process_dob_date(row['dob.date'])
                row['registered.date'] = process_register_date(row['registered.date'])
                row['global_index'] = idx
                row['current_time'] = calculate_current_time(row['location.timezone.offset'])

                writer.writerow(row)
                row_count += 1

                if row_limit and row_count >= row_limit:
                    break

        logger.info(f"Успішно оброблено {row_count} рядків до {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Помилка обробки файлу CSV: {str(e)}")
        raise


def create_folder_structure(data, destination_folder):
    # Create folder structure and save data to appropriate files
    logger = logging.getLogger('user_data_processor')
    logger.info("Створення структури папок і збереження даних")

    # Group data by decade and country
    decade_country_data = defaultdict(lambda: defaultdict(list))

    for row in data:
        try:
            # Extract decade from dob.date
            dob_parts = row['dob.date'].split('/')
            if len(dob_parts) == 3:
                year = int(dob_parts[2])
                decade = f"{(year // 10) * 10}-th"
                country = row['location.country'] if 'location.country' in row else row.get('nat', 'Unknown')
                decade_country_data[decade][country].append(row)
        except Exception as e:
            logger.warning(f"Помилка обробки рядка для структури папок: {str(e)}")
            continue

    created_files = []

    # Remove data before 1960s
    for decade in list(decade_country_data.keys()):
        if int(decade.split('-')[0]) < 1960:
            del decade_country_data[decade]

    # Create folder structure and save files
    for decade, countries in decade_country_data.items():
        decade_folder = os.path.join(destination_folder, decade)
        os.makedirs(decade_folder, exist_ok=True)

        for country, users in countries.items():
            country_folder = os.path.join(decade_folder, country)
            os.makedirs(country_folder, exist_ok=True)

            # Calculate stats for filename
            ages = []
            registration_years = []
            id_names = defaultdict(int)

            for user in users:
                try:
                    # Calculate age
                    dob_parts = user['dob.date'].split('/')
                    if len(dob_parts) == 3:
                        birth_year = int(dob_parts[2])
                        current_year = datetime.datetime.now().year
                        ages.append(current_year - birth_year)

                    # Calculate registration years
                    reg_parts = user['registered.date'].split(',')[0].split('-')
                    if len(reg_parts) == 3:
                        reg_year = int(reg_parts[2])
                        current_year = datetime.datetime.now().year
                        registration_years.append(current_year - reg_year)

                    # Count id names
                    if 'id.name' in user:
                        id_names[user['id.name']] += 1
                except Exception as e:
                    logger.warning(f"Помилка підрахунку статистики для користувача: {str(e)}")
                    continue

            max_age = max(ages) if ages else 0
            avg_registered = sum(registration_years) / len(registration_years) if registration_years else 0
            popular_id = max(id_names.items(), key=lambda x: x[1])[0] if id_names else 'unknown'

            # Create filename
            filename = f"max_age_{max_age}_avg_registered_{avg_registered:.1f}_popular_id_{popular_id}.csv"
            filepath = os.path.join(country_folder, filename)

            # Save data to file
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                if users:
                    writer = csv.DictWriter(f, fieldnames=users[0].keys())
                    writer.writeheader()
                    writer.writerows(users)

            created_files.append(filepath)
            logger.info(f"Створений файл: {filepath}")

    return created_files


def log_folder_structure(destination_folder):
    # log the folder structure with tabulation and file flags
    logger = logging.getLogger('user_data_processor')
    logger.info("Структура папок:")

    for root, dirs, files in os.walk(destination_folder):
        level = root.replace(destination_folder, '').count(os.sep)
        indent = ' ' * 4 * level
        logger.info(f"{indent}{os.path.basename(root)}/ [folder]")

        subindent = ' ' * 4 * (level + 1)
        for f in files:
            logger.info(f"{subindent}{f} [file]")


def create_zip_archive(source_folder, output_filename):
    logger = logging.getLogger('user_data_processor')
    logger.info(f"Створення zip-архіву: {output_filename}")

    try:
        shutil.make_archive(output_filename, 'zip', source_folder)
        logger.info(f"ZIP-архів успішно створено: {output_filename}.zip")
        return f"{output_filename}.zip"
    except Exception as e:
        logger.error(f"Помилка створення zip-архіву: {str(e)}")
        raise


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process user data from randomuser.me')
    parser.add_argument('destination', help='Path to destination folder (required)')
    parser.add_argument('--filename', default='output', help='Output filename (default: output)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--gender', help='Filter data by gender')
    group.add_argument('--rows', type=int, help='Filter by number of rows')
    parser.add_argument('log_level', nargs='?', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Set up logger
    numeric_level = getattr(logging, args.log_level.upper(), None)
    logger = setup_logger(numeric_level)

    try:
        # Create destination folder if it doesn't exist
        destination_folder = os.path.abspath(args.destination)
        os.makedirs(destination_folder, exist_ok=True)
        os.chdir(destination_folder)
        logger.info(f"Для робочого каталогу встановлено значення: {destination_folder}")

        # Download data
        initial_file = f"initial_{args.filename}.csv"
        downloaded_file = download_user_data(5000, initial_file)

        # Process CSV
        processed_file = f"processed_{args.filename}.csv"
        process_csv(downloaded_file, processed_file, args.gender, args.rows)

        # Read processed data
        with open(processed_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)

        # Create folder structure and save data
        create_folder_structure(data, destination_folder)

        # Log folder structure
        log_folder_structure(destination_folder)

        # Create zip archive
        zip_filename = f"user_data_{int(time.time())}"
        create_zip_archive(destination_folder, zip_filename)

        logger.info("Обробку успішно завершено")

    except Exception as e:
        logger.critical(f"Помилка сценарію: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()