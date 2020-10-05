import sqlite3


class SQLLite:
    """View DB
    name db: parameter,

    table:
    CREATE TABLE Users (
    id                INTEGER       PRIMARY KEY AUTOINCREMENT,
    id_user           VARCHAR (30)  NOT NULL,
    number_of_request INTEGER       NOT NULL
                                    DEFAULT (0),
    first_name        VARCHAR (255) NOT NULL,
    last_name         VARCHAR (255) NOT NULL
    );
"""

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def user_exists(self, id_user):
        """Проверяем, есть ли пользователь в базе данных"""
        with self.connection:
            result = self.cursor.execute('SELECT "number_of_request" FROM "Users" WHERE "id_user" = ?',
                                         (id_user,)).fetchall()
            return bool(len(result))

    def add_user(self, id_user, first_name, last_name):
        """Добавляем пользователя в базу"""
        with self.connection:
            return self.cursor.execute('INSERT INTO "Users" ("id_user", "first_name", "last_name") VALUES(?,?,?)',
                                       (id_user, first_name, last_name))

    def update_status(self, id_user):
        with self.connection:
            number = int(self.cursor.execute('SELECT "number_of_request" FROM "Users" WHERE "id_user" = ?',
                                             (id_user,)).fetchall()[0][0]) + 1
            return self.cursor.execute(
                'UPDATE "Users" SET "number_of_request" = ? WHERE "id_user" = ?',
                (str(number), id_user))

    def get_status(self, id_user):
        with self.connection:
            number = self.cursor.execute('SELECT "number_of_request" FROM "Users" WHERE "id_user" = ?',
                                         (id_user,)).fetchall()

            return number[0][0]


if __name__ == '__main__':
    pass
