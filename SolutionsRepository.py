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
        self.connection.autocommit = True

    def mark_solution_obsolete(self, schema_id: int) -> None:
        cursor = self.connection.cursor()
        if not self.solution_exists(schema_id):
            raise Exception(f"Solution with schema_id {schema_id} does not exist.")
        query = """
        UPDATE solution
        SET status_id = (SELECT id FROM solution_status WHERE name = 'obsolete')
        WHERE schema_id = %s
        """
        cursor.execute(query, (schema_id,))
        cursor.close()
        self.connection.commit()

    def mark_solution_actual(self, schema_id: int) -> None:
        cursor = self.connection.cursor()
        if not self.solution_exists(schema_id):
            raise Exception(f"Solution with schema_id {schema_id} does not exist.")
        query = """
        UPDATE solution
        SET status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        WHERE schema_id = %s
        """
        cursor.execute(query, (schema_id,))
        cursor.close()
        self.connection.commit()

    def solution_exists(self, schema_id: int) -> bool:
        cursor = self.connection.cursor()
        query = """
        SELECT COUNT(*)
        FROM solution
        WHERE schema_id = %s
        """
        cursor.execute(query, (schema_id,))
        solutions_count = cursor.fetchone()[0]
        cursor.close()
        return solutions_count > 0

    def has_actual_solution(self, schema_id: int) -> bool:
        cursor = self.connection.cursor()
        query = """
        SELECT COUNT(*)
        FROM solution
        WHERE schema_id = %s AND status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        """
        cursor.execute(query, (schema_id,))
        actual_solutions_count = cursor.fetchone()[0]
        print("Actual solutions count for schema with id " + str(schema_id) + ": " + str(actual_solutions_count))
        cursor.close()
        return actual_solutions_count > 0

    def set_solution(self, schema_id: int, solution: str) -> None:
        cursor = self.connection.cursor()
        if self.has_actual_solution(schema_id):
            self.mark_solution_obsolete(schema_id)

        query = """
        INSERT INTO solution (schema_id, solution_json, status_id)
        VALUES (%s, %s, (SELECT id FROM solution_status WHERE name = 'actual'))
        ON DUPLICATE KEY UPDATE solution_json 
        = VALUES(solution_json), status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        """
        cursor.execute(query, (schema_id, solution))
        cursor.close()
        self.connection.commit()

    def get_solution(self, schema_id: int) -> str:
        cursor = self.connection.cursor()
        query = """
        SELECT solution_json
        FROM solution
        WHERE schema_id = %s AND status_id = (SELECT id FROM solution_status WHERE name = 'actual')
        """
        cursor.execute(query, (schema_id,))
        result = cursor.fetchone()
        cursor.close()
        if not result:
            raise Exception(f"Solution with schema_id {schema_id} does not exist or is obsolete.")
        return result[0]

    def __del__(self):
        self.connection.close()



