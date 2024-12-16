import mysql.connector

# Функция для подключения к базе данных MySQL
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',  # Хост базы данных
            database='bot',  # Имя базы данных
            user='root',  # Имя пользователя
            password='1234'  # Пароль
        )
        return connection
    except Exception as e:
        print(f'Ошибка подключения к базе данных: {e}')
        return None

# Функция для создания таблицы, если она не существует
def create_table():
    connection = create_connection()
    if connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS user_routes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    route TEXT NOT NULL,
                    gpx_data LONGTEXT NOT NULL
                )
                '''
            )
        connection.commit()
        connection.close()

# Функция для записи id пользователя, маршрута и содержимого GPX файла в базу данных
def insert_user_route(user_id: int, route: str, gpx_data: str):
    connection = None
    try:
        connection = create_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO user_routes (user_id, route, gpx_data)
                VALUES (%s, %s, %s)
                ''', (user_id, route, gpx_data)
            )
        connection.commit()
    except Exception as e:
        print(f'Ошибка при вставке данных: {e}')
    finally:
        if connection:
            connection.close()

# Создаем таблицу при запуске модуля
create_table()