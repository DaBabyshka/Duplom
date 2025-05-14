import sqlite3

# Подключение к базе данных (если не существует, она будет создана)
conn = sqlite3.connect('real_estate.db')
cursor = conn.cursor()

# Создание таблицы
cursor.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        year INTEGER NOT NULL,
        average_price REAL NOT NULL,
        description TEXT,
        wiki_link TEXT
    );
''')

# Вставка данных
cursor.executemany('''
    INSERT INTO prices (city, year, average_price, description, wiki_link) 
    VALUES (?, ?, ?, ?, ?);
''', [
    ('Калининград', 2020, 55000, 'Калининград — город в России, административный центр Калининградской области.', 'https://ru.wikipedia.org/wiki/Калининград'),
    ('Калининград', 2021, 60000, 'Калининград — город с богатой историей и архитектурой.', 'https://ru.wikipedia.org/wiki/Калининград'),
    ('Калининград', 2022, 65000, 'Калининград известен своими пляжами и морским климатом.', 'https://ru.wikipedia.org/wiki/Калининград'),
    ('Калининград', 2023, 70000, 'Город развивается, привлекая инвестиции в недвижимость.', 'https://ru.wikipedia.org/wiki/Калининград'),
    ('Калининград', 2024, 75000, 'Продолжающийся рост цен в Калининграде из-за спроса на жильё.', 'https://ru.wikipedia.org/wiki/Калининград'),

    ('Москва', 2020, 120000, 'Москва — столица России, крупнейший культурный и экономический центр страны.', 'https://ru.wikipedia.org/wiki/Москва'),
    ('Москва', 2021, 125000, 'Москва — центр финансов и деловой активности.', 'https://ru.wikipedia.org/wiki/Москва'),
    ('Москва', 2022, 130000, 'Город развивается, строятся новые жилые комплексы.', 'https://ru.wikipedia.org/wiki/Москва'),
    ('Москва', 2023, 135000, 'Высокие цены на недвижимость из-за спроса и ограниченного предложения.', 'https://ru.wikipedia.org/wiki/Москва'),
    ('Москва', 2024, 140000, 'Продолжающийся рост цен на жильё в Москве.', 'https://ru.wikipedia.org/wiki/Москва'),

    # Добавьте другие города по аналогии
])

# Подтверждаем изменения и закрываем соединение
conn.commit()
conn.close()

print("База данных создана и данные вставлены!")
