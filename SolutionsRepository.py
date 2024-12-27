from abc import ABC, abstractmethod
import mysql.connector


class SolutionsRepository(ABC):

    # If solution exists, marks it as obsolete
    # If solution does not exist, throws an exception
    @abstractmethod
    def mark_solution_obsolete(self, schema_id: int) -> None:
        pass

    # If solution exists, marks it as actual
    # If solution does not exist, throws an exception
    @abstractmethod
    def mark_solution_actual(self, schema_id: int) -> None:
        pass

    # Returns false if solution does not exist or is obsolete
    # Returns true if solution exists and is actual
    @abstractmethod
    def has_actual_solution(self, schema_id: int) -> bool:
        pass

    # If solution exists, replaces it with the new one
    # If solution does not exist, creates a new one
    @abstractmethod
    def set_solution(self, schema_id: int, solution: str) -> None:
        pass

    # If solution exists, returns it
    # If solution does not exist, throws an exception
    @abstractmethod
    def get_solution(self, schema_id: int) -> str:
        pass


class MySQLSolutionsRepository(SolutionsRepository):

    def __init__(self, host, user, password, database):
        self.connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.connection.cursor()

    def mark_solution_obsolete(self, schema_id: int) -> None:
        if not self.solution_exists(schema_id):
            raise Exception(f"Solution with schema_id {schema_id} does not exist.")
        query = """
        UPDATE solution
        SET status_id = (SELECT id FROM solution_status WHERE name = 'obsolete')
        WHERE schema_id = %s
        """
        self.cursor.execute(query, (schema_id,))
        self.connection.commit()

    def mark_solution_actual(self, schema_id: int) -> None:
        if not self.solution_exists(schema_id):
            raise Exception(f"Solution with schema_id {schema_id} does not exist.")
        query = """
        UPDATE solution
        SET status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        WHERE schema_id = %s
        """
        self.cursor.execute(query, (schema_id,))
        self.connection.commit()

    def solution_exists(self, schema_id: int) -> bool:
        query = """
        SELECT COUNT(*)
        FROM solution
        WHERE schema_id = %s
        """
        self.cursor.execute(query, (schema_id,))
        return self.cursor.fetchone()[0] > 0

    def has_actual_solution(self, schema_id: int) -> bool:
        query = """
        SELECT COUNT(*)
        FROM solution
        WHERE schema_id = %s AND status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        """
        self.cursor.execute(query, (schema_id,))
        return self.cursor.fetchone()[0] > 0

    def set_solution(self, schema_id: int, solution: str) -> None:
        if self.has_actual_solution(schema_id):
            self.mark_solution_obsolete(schema_id)

        query = """
        INSERT INTO solution (schema_id, solution_json, status_id)
        VALUES (%s, %s, (SELECT id FROM solution_status WHERE name = 'actual'))
        ON DUPLICATE KEY UPDATE solution_json = VALUES(solution_json), status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        """
        self.cursor.execute(query, (schema_id, solution))
        self.connection.commit()

    def get_solution(self, schema_id: int) -> str:
        query = """
        SELECT solution_json
        FROM solution
        WHERE schema_id = %s AND status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        """
        self.cursor.execute(query, (schema_id,))
        result = self.cursor.fetchone()
        if not result:
            raise Exception(f"Solution with schema_id {schema_id} does not exist or is obsolete.")
        return result[0]

    def __del__(self):
        self.cursor.close()
        self.connection.close()
