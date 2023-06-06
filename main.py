from bottle import Bottle
import threading
from FeatureCloud.app.api.http_ctrl import api_server
from FeatureCloud.app.api.http_web import web_server

from FeatureCloud.app.engine.app import App
import os

import myapp
import states
import utils
from myapp import MyApp, APP_NAME

server = Bottle()


def run_app():
    server.mount('/api', api_server)
    server.mount('/web', web_server)
    server.run(host='localhost', port=5000)


if __name__ == '__main__':
    config = utils.read_config()[myapp.APP_NAME]
    if utils.is_native():

        print("Native")
        if utils.is_simulation(myapp.APP_NAME):
            print(f"Simulated: {config['simulation']}")

            threads = []
            clients = {}
            clients_ids = [id.strip() for id in config['simulation']['clients'].split(',')]
            clients_dirs = config['simulation']['clients_dir'].split(',')
            simulation_dir = config['simulation'].get('dir', None)
            simulation_dir = simulation_dir if simulation_dir else ''
            controller = utils.Controller(clients_ids)
            # shared_memory = utils.SharedMemory(clients_ids)
            for i, (client_id, client_dir) in enumerate(zip(clients_ids, clients_dirs)):
                app = App()
                client = states.create_client(
                    MyApp(config=utils.read_config()[APP_NAME],
                          simulation_dir=f"{simulation_dir}/{client_dir}")
                    , app
                )
                controller.register(client_id, app, coordinator=i == 0)
            controller.run()
                # t = threading.Thread(target=utils.run_client, args=(app, client_id, clients_ids, i == 0, shared_memory))
                # threads.append(t)
                # t.start()
                # coordinator_role = i == 0
                # clients[client_id] = App()
                # states.create_client(
                #     MyApp(config=utils.read_config()[APP_NAME],
                #           simulation_dir=f"{simulation_dir}/{client_dir}")
                #     , clients[client_id]
                # )
                # clients[client_id].register()
                # clients[client_id].handle_setup(client_id=client_id,
                #                                 coordinator=coordinator_role,
                #                                 clients=clients_ids)
        else:
            print("Centralized")
            general_app_instance = App()
            states.create_client(
                MyApp(
                    config=utils.read_config()[APP_NAME],
                    simulation_dir=None
                )
                , general_app_instance, centralized=True
            )
            general_app_instance.register()
            general_app_instance.handle_setup(client_id='1', coordinator=True, clients=['1'])
    else:
        run_app()
