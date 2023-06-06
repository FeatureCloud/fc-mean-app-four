from FeatureCloud.app.engine.app import AppState, app_state, Role
import myapp
import utils
from time import sleep
from threading import Lock

lock = Lock()
# print(f"{'Centralized' if utils.is_centralized(myapp.APP_NAME) else 'Federated'},"
#       f" {'Native' if utils.is_native() else 'Containerized'},"
#       f" {'Simulation' if utils.is_simulation(myapp.APP_NAME) else 'Multiple Containers'}")


network_buffer = {}


def create_client(target_app_instance, general_app_instance, centralized=False):
    if centralized:
        return generate_centralized_states(general_app_instance, target_app_instance)
    return generate_federated_states(general_app_instance, target_app_instance)


def generate_federated_states(general_app_instance, target_app_instance):
    @app_state(name='initial', role=Role.BOTH, app_instance=general_app_instance)
    class InitialState(AppState):
        def register(self):
            self.register_transition('Local_Training')

        def run(self):
            data_to_broadcast = target_app_instance.load_data()
            if self.is_coordinator:
                if data_to_broadcast:
                    # broadcast_data(self, data_to_broadcast)
                    self.broadcast_data(data_to_broadcast)
                else:
                    self.broadcast_data(None)

            return 'Local_Training'

    @app_state('Local_Training', app_instance=general_app_instance)
    class LocalTraining(AppState):

        def register(self):
            self.register_transition('Global_Aggregation', role=Role.COORDINATOR)
            self.register_transition('Local_Training', role=Role.PARTICIPANT)
            self.register_transition('Write_Results', role=Role.BOTH)

        def run(self):
            # received_data = await_data(self)
            received_data = self.await_data()
            received_data = received_data if received_data else None
            data_to_send = target_app_instance.local_training(global_parameters=received_data)
            self.log(data_to_send)
            # if self.data_to_send is None:
            #     raise NotImplementedError("Local_Training is expected to have some local parameters to share")
            # send_data_to_coordinator(self,
            #                          data_to_send,
            #                          use_smpc=target_app_instance.config["use_smpc"])
            self.send_data_to_coordinator(data_to_send,
                                          use_smpc=target_app_instance.config["use_smpc"])
            if target_app_instance.last_round:
                return "Write_Results"
            if self.is_coordinator:
                return "Global_Aggregation"
            return "Local_Training"

    @app_state('Global_Aggregation', app_instance=general_app_instance)
    class GlobalAggregation(AppState):

        def register(self):
            self.register_transition('Local_Training', role=Role.COORDINATOR)

        def run(self):
            if target_app_instance.config['use_smpc']:
                # local_data = aggregate_data(self)
                local_data = self.aggregate_data()
            else:
                # local_data = gather_data(self)
                local_data = self.gather_data()
                print("GG", local_data)
            data_to_broadcast = target_app_instance.global_aggregation(local_parameters=local_data)
            # if self.data_to_broadcast is None:
            #     raise NotImplementedError("Global_Aggregation is expected to have some local parameters to share")
            self.broadcast_data(data_to_broadcast)
            return 'Local_Training'

    @app_state('Write_Results', app_instance=general_app_instance)
    class WriteResults(AppState):

        def register(self):
            self.register_transition('terminal')

        def run(self):
            target_app_instance.write_results()
            return 'terminal'

    return general_app_instance


def generate_centralized_states(general_app_instance, target_app_instance):
    @app_state(name='initial', role=Role.BOTH, app_instance=general_app_instance)
    class InitialState(AppState):

        def register(self):
            self.register_transition('Centralized')

        def run(self):
            return 'Centralized'

    @app_state('Centralized', app_instance=general_app_instance)
    class Centralized(AppState):

        def register(self):
            self.register_transition('terminal')

        def run(self):
            target_app_instance.centralized()
            return 'terminal'

    return general_app_instance


# def broadcast_data(obj, data):
#     print(obj.clients)
#     if utils.is_native():
#         for client in obj.clients:
#             obj._app.shared_memory.update(client, data)
#
#         # global network_buffer
#         # lock.acquire()
#         # for client in obj.clients:
#         #     print(client)
#         #     update_buffer(client, data)
#         # lock.release()
#
#     else:
#         obj.broadcast_data(data)
#
#
# def send_data_to_coordinator(obj, data, use_smpc):
#     if utils.is_native():
#         obj._app.shared_memory.update(obj.clients[0], data)
#         # global network_buffer
#         # # lock.acquire()
#         # if obj.clients[0] in network_buffer:
#         #     network_buffer[obj.clients[0]].append(data)
#         # else:
#         #     network_buffer[obj.clients[0]] = [data]
#         # lock.release()
#     else:
#         obj.broadcast(data, use_smpc)
#
#
# def aggregate_data(obj):
#     if utils.is_native():
#         while True:
#             data = obj._app.shared_memory.read(obj.id)
#             if len(data) == len(obj.clients):
#                 return obj._app.shared_memory.pop(obj.id)
#             sleep(3)
#         # global network_buffer
#         # while True:
#         #     data = check_buffer(obj.id, pop=False)
#         #     if data:
#         #         if len(data) == len(obj.clients):
#         #             return check_buffer(obj.id)
#         #     sleep(3)
#     else:
#         return obj.aggregate_data(use_smpc=True)
#
#
# def gather_data(obj):
#     if utils.is_native():
#         while True:
#             data = obj._app.shared_memory.read(obj.id)
#             if len(data) == len(obj.clients):
#                 return obj._app.shared_memory.pop(obj.id)
#             sleep(3)
#         # global network_buffer
#         # while True:
#         #     data = check_buffer(obj.id, pop=False)
#         #     if data:
#         #         if len(data) == len(obj.clients):
#         #             return check_buffer(obj.id)
#         #     sleep(3)
#     return obj.gather_data()
#
#
# def await_data(obj):
#     if utils.is_native():
#         obj._app.shared_memory.pop(obj.id)
#         # while True:
#         #     print(obj.id)
#         #     data = check_buffer(obj.id, pop=False)
#         #     if data:
#         #         return check_buffer(obj.id)
#         #     sleep(3)
#         #     print("data received")
#     return obj.await_data()

# def update_buffer(key, value):
#     global network_buffer, lock
#     while True:
#         if not lock.acquire(False):
#             lock.acquire()
#             break
#     if key not in network_buffer:
#         network_buffer[key] = [value]
#     else:
#         network_buffer[key].append(value)
#     lock.release()


# def check_buffer(key, pop=True):
#     global network_buffer
#     lock = obj._app.thread.
#     print("check buffer")
#     while True:
#         if not lock.acquire(False):
#             print("acquire")
#             lock.acquire()
#             break
#         sleep(3)
#     data = None
#     if key in network_buffer:
#         if pop:
#             data = network_buffer.pop(key)
#         else:
#             data = network_buffer[key]
#     lock.release()
#     print("release")
#     return data
