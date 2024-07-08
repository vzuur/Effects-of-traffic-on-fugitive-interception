import logging
import pickle
import random
import time

import networkx as nx
import osmnx as ox

from basic_logger import get_module_logger
from plot_results import plot_routes
from pydsol.core.experiment import SingleReplication
from pydsol.core.simulator import DEVSSimulatorFloat
from model_hot import FugitiveModel

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s (%(name)s - %(filename)s: line %(lineno)s)')

logger = get_module_logger(__name__, level=logging.INFO)

if __name__ == '__main__':
    mode = 'hot'
    seed = 112
    random.seed(seed)
    run_length = 1800  # 30 minutes

    for city in ['Rotterdam']:
        for location in ['centre', 'port']:
            print('bezig met locatie', location)
            with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
                escape_nodes = pickle.load(f)

            with open(f'data/fugitive_start_{city}_{location}.pkl', 'rb') as f:
                fugitive_start = pickle.load(f)

            graph = ox.load_graphml(filepath=f"graphs/{city}_withouttraffic_prepped_hot.graph.graphml")

            # convert strings to floats in attributes
            travel_time_dict = {}
            for u, v, z, data in graph.edges(data=True,keys=True):
                if 'travel_time_adj' in data.keys():
                    travel_time_dict[(u, v, z)] = float(data['travel_time_adj'])
                else:
                    travel_time_dict[(u, v, z)] = float(data['travel_time'])
            nx.set_edge_attributes(graph, travel_time_dict, "travel_time_adj")

            # for jitter in [0, 0.01, 0.02, 0.05, 0.1]:
            for jitter in [0.02]:
                # generate shortest paths for ABM
                # # TODO import these instead of generating each time
                # route_fugitive = []
                # while len(route_fugitive) < 1000:
                #     for escape_node in escape_nodes:
                #         try:
                #             path = nx.shortest_path(graph, fugitive_start, escape_node, 'travel_time_adj')
                #             # [escape_routes.append(path) for path in nx.all_simple_paths(G, fugitive_start, escape_node)]
                #             route_fugitive.append(path)
                #         except:
                #             continue
                #
                # else:
                #     AttributeError

                with open(f'data/escape_routes_{city}_hot_{location}_withouttraffic.pkl', 'rb') as f:
                    route_fugitive = pickle.load(f)

                # instatiate model
                simulator = DEVSSimulatorFloat("sim")
                model = FugitiveModel(simulator=simulator,
                                      input_params={'seed': seed,
                                                    'graph': graph,
                                                    'start_fugitive': fugitive_start,
                                                    'route_fugitive': route_fugitive,
                                                    'num_fugitive_routes': len(route_fugitive),
                                                    'jitter': jitter,
                                                    'escape_nodes': escape_nodes,
                                                    },
                                      seed=seed)

                replication = SingleReplication(str(0), 0.0, 0.0, run_length)
                # experiment = Experiment("test", simulator, sim_model, 0.0, 0.0, 700, nr_replications=5)
                simulator.initialize(model, replication)
                simulator.start()
                # Python wacht niet todat de simulatie voorbij is, vandaar deze while loop
                while simulator.simulator_time < run_length:
                    time.sleep(0.01)

                routes = model.get_output_statistics()

                ratio_tt = ''
                with open(f'data/results_routes_{mode}_{city}_jitter{jitter}_{location}_withouttraffic.pkl', 'wb') as f:
                    pickle.dump(routes, f)

                #plot_routes(city, mode, jitter, location)

                model.reset_model()
