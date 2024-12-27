from fastapi import FastAPI
from SolutionsRepository import MySQLSolutionsRepository
from Solver import Solver
from model import Schema

app = FastAPI()
solver = Solver()
solutions_repository = MySQLSolutionsRepository(
    host="localhost", user="root", password="root", database="solutions_service")


@app.put("/mark_solution_obsolete/{schema_id}")
async def mark_solution_obsolete(schema_id: int):
    try:
        if not solutions_repository.has_actual_solution(schema_id):
            print(f"No actual solution for schema {schema_id}")
            return {"message": f"No actual solution for schema {schema_id}"}
        solutions_repository.mark_solution_obsolete(schema_id)
        print(f"Solution for schema {schema_id} marked as obsolete")
        return {"message": f"Solution for schema {schema_id} marked as obsolete"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/has_actual_solution/{schema_id}")
async def has_actual_solution(schema_id: int):
    return {"has_actual_solution": solutions_repository.has_actual_solution(schema_id)}


@app.post("/solve")
async def solve(schema: Schema):
    try:
        schema_id = schema.id
        if solutions_repository.has_actual_solution(schema_id):
            print(f"Solution for schema {schema_id} already exists")
            solution_str = solutions_repository.get_solution(schema_id)
            solution = eval(solution_str)
            return {"solution": solution}
        solution = solver.solve(schema)
        solution_str = str(solution)
        solutions_repository.set_solution(schema_id, solution_str)
        solutions_repository.mark_solution_actual(schema_id)
        print(f"Solution for schema {schema_id} created and marked as actual")
        return {"solution": solution}
    except Exception as e:
        return {"error": str(e)}
