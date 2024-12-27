from pyvrp import Model, Client
from pyvrp.stop import MaxRuntime

from model import Schema


class Solver:

    def solve(self, schema: Schema):
        m = Model()

        # Setting AMR parameters
        amr_parameters = schema.get_amr_parameters()
        m.add_vehicle_type(num_available=amr_parameters.get_quantity(),
                           capacity=int(amr_parameters.get_capacity()))

        # Creating depot
        depot = m.add_depot(0, 0)

        # Configuring clients (workstations)
        workstations = schema.get_all_workstations()
        clients = {}  # This dictionary will be used to map workstations names to client objects
        clients_names: [str] = []  # This list will be used to map clients numbers to workstations names
        for workstation in workstations:
            client = m.add_client(int(workstation.x), int(workstation.y), delivery=int(workstation.demand),
                                  name=workstation.name)
            clients[workstation.name] = client
            clients_names.append(workstation.name)
            m.add_edge(frm=depot, to=client, distance=int(workstation.depot_distance))
            m.add_edge(frm=client, to=depot, distance=int(workstation.depot_distance))
        transport_costs = schema.get_transportation_costs()
        for transport_cost in transport_costs:
            from_client = clients[transport_cost.get_from().name]
            to_client = clients[transport_cost.get_to().name]
            cost = transport_cost.get_cost()
            m.add_edge(frm=from_client, to=to_client, distance=int(cost))
            m.add_edge(frm=to_client, to=from_client, distance=int(cost))

        res = m.solve(stop=MaxRuntime(1), display=True)
        solution = {}
        i = 0
        for route in res.best.routes():
            solution[i] = []
            for visit in route.visits():
                client_name = clients_names[visit - 1]
                solution[i].append(client_name)
            i += 1

        return solution
