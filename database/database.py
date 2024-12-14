import psycopg2
from psycopg2 import sql

# Функция для подключения к базе данных PostgreSQL
def create_connection():
    try:
        connection = psycopg2.connect(
            dbname='bot',  # Замените на имя вашей базы данных
            user='postgres',    # Замените на имя пользователя
            password='bmw330mm', # Замените на пароль
            host='localhost',         # Хост базы данных
            port='5432'               # Порт подключения
        )
        return connection
    except Exception as e:
        print(f'Ошибка подключения к базе данных: {e}')
        return None

# Функция для создания таблицы, если она не существует
def create_table():
    connection = create_connection()
    if connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS user_routes (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        route TEXT NOT NULL
                    )
                    '''
                )
        connection.close()

# Функция для записи id пользователя и маршрута в базу данных
def insert_user_route(user_id: int, route: str):
    connection = None
    try:
        connection = create_connection()
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO user_routes (user_id, route)
                    VALUES (%s, %s)
                    ''', (user_id, route)
                )
    except Exception as e:
        print(f'Ошибка при вставке данных: {e}')
    finally:
        if connection:
            connection.close()

# Создаем таблицу при запуске модуля
create_table()