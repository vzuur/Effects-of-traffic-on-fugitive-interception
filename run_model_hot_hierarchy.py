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

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s (%(name)s - %(filename)s: line %(lineno)s)')

logger = get_module_logger(__name__, level=logging.INFO)

if __name__ == '__main__':
    for city in ['Utrecht']:
    # for city in ['Amsterdam']:
    # for city in ['Manhattan']:
        for seconds_till_hot in [120, 60, 20, 0]:
            for ratio_tt in [-0.2, 0.3, 0.7]:
                # city = 'Manhattan'
                # jitter = 0.1
                mode = 'hot'

                seed = 112
                random.seed(seed)

                with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
                    escape_nodes = pickle.load(f)

                with open(f'data/fugitive_start_{city}.pkl', 'rb') as f:
                    fugitive_start = pickle.load(f)

                if mode == 'hot':
                    from model_hot import FugitiveModel

                    # graph = ox.load_graphml(filepath=f"graphs/{city}_prepped_hot.graph.graphml")
                    graph = ox.load_graphml(filepath=f"graphs/{city}_prepped.graph.graphml")
                    run_length = 1800  # 5minutes for testing
                    jitter = seconds_till_hot  # for filename purposes

                    # generate shortest paths for ABM
                    route_fugitive = []
                    while len(route_fugitive) < 100:
                        for escape_node in escape_nodes:
                            try:
                                path = nx.shortest_path(graph, fugitive_start, escape_node, 'travel_time')
                                # [escape_routes.append(path) for path in nx.all_simple_paths(G, fugitive_start, escape_node)]
                                route_fugitive.append(path)
                            except:
                                continue
                    print('constructed escape routes')

                elif mode == 'cool':
                    from model_cool import FugitiveModel

                    graph = ox.load_graphml(filepath=f"graphs/{city}_prepped.graph.graphml")
                    run_length = 1800  # 30 minutes

                    # with open(f'data/escape_routes_{city}.pkl', 'rb') as f:
                    #     route_fugitive = pickle.load(f)

                    # generate shortest paths for ABM
                    route_fugitive = []
                    while len(route_fugitive) < 1000:
                        for escape_node in escape_nodes:
                            try:
                                path = nx.shortest_path(graph, fugitive_start, escape_node, 'travel_time')
                                # [escape_routes.append(path) for path in nx.all_simple_paths(G, fugitive_start, escape_node)]
                                route_fugitive.append(path)
                            except:
                                continue

                else:
                    AttributeError

                travel_time_dict = {}
                for u, v, data in graph.edges(data=True):
                    if 'travel_time_adj' in data.keys():
                        travel_time_dict[(u, v, 0)] = float(data['travel_time_adj'])
                    else:
                        travel_time_dict[(u, v, 0)] = float(data['travel_time'])
                nx.set_edge_attributes(graph, travel_time_dict, "travel_time_adj")

                simulator = DEVSSimulatorFloat("sim")
                model = FugitiveModel(simulator=simulator,
                                      input_params={'seed': seed,
                                                    'graph': graph,
                                                    'start_fugitive': fugitive_start,
                                                    'route_fugitive': route_fugitive,
                                                    'num_fugitive_routes': len(route_fugitive),
                                                    'jitter': jitter,
                                                    'escape_nodes': escape_nodes,
                                                    'seconds_till_hot': seconds_till_hot,
                                                    'ratio_tt': ratio_tt,
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

                with open(f'data/results_routes_{mode}_{city}_jitter{jitter}_ratio_tt{ratio_tt}.pkl', 'wb') as f:
                    pickle.dump(routes, f)

                plot_routes(city, mode, jitter, ratio_tt)

                model.reset_model()

    for city in ['Utrecht', 'Winterswijk', 'Manhattan']:
        for seconds_till_hot in [0, 20, 60, 120]:
            for ratio_tt in [0, 0.1, 0.2, 0.4, 0.5]:
                # city = 'Manhattan'
                # jitter = 0.1
                mode = 'hot'

                seed = 112
                random.seed(seed)

                with open(f'data/escape_nodes_{city}.pkl', 'rb') as f:
                    escape_nodes = pickle.load(f)

                with open(f'data/fugitive_start_{city}.pkl', 'rb') as f:
                    fugitive_start = pickle.load(f)

                if mode == 'hot':
                    from model_hot import FugitiveModel

                    # graph = ox.load_graphml(filepath=f"graphs/{city}_prepped_hot.graph.graphml")
                    graph = ox.load_graphml(filepath=f"graphs/{city}_prepped.graph.graphml")
                    run_length = 1800  # 5minutes for testing
                    jitter = seconds_till_hot  # for filename purposes

                    # generate shortest paths for ABM
                    route_fugitive = []
                    while len(route_fugitive) < 100:
                        for escape_node in escape_nodes:
                            try:
                                path = nx.shortest_path(graph, fugitive_start, escape_node, 'travel_time')
                                # [escape_routes.append(path) for path in nx.all_simple_paths(G, fugitive_start, escape_node)]
                                route_fugitive.append(path)
                            except:
                                continue

                elif mode == 'cool':
                    from model_cool import FugitiveModel

                    graph = ox.load_graphml(filepath=f"graphs/{city}_prepped.graph.graphml")
                    run_length = 1800  # 30 minutes

                    # with open(f'data/escape_routes_{city}.pkl', 'rb') as f:
                    #     route_fugitive = pickle.load(f)

                    # generate shortest paths for ABM
                    route_fugitive = []
                    while len(route_fugitive) < 1000:
                        for escape_node in escape_nodes:
                            try:
                                path = nx.shortest_path(graph, fugitive_start, escape_node, 'travel_time')
                                # [escape_routes.append(path) for path in nx.all_simple_paths(G, fugitive_start, escape_node)]
                                route_fugitive.append(path)
                            except:
                                continue

                else:
                    AttributeError

                travel_time_dict = {}
                for u, v, data in graph.edges(data=True):
                    if 'travel_time_adj' in data.keys():
                        travel_time_dict[(u, v, 0)] = float(data['travel_time_adj'])
                    else:
                        travel_time_dict[(u, v, 0)] = float(data['travel_time'])
                nx.set_edge_attributes(graph, travel_time_dict, "travel_time_adj")

                simulator = DEVSSimulatorFloat("sim")
                model = FugitiveModel(simulator=simulator,
                                      input_params={'seed': seed,
                                                    'graph': graph,
                                                    'start_fugitive': fugitive_start,
                                                    'route_fugitive': route_fugitive,
                                                    'num_fugitive_routes': len(route_fugitive),
                                                    'jitter': jitter,
                                                    'escape_nodes': escape_nodes,
                                                    'seconds_till_hot': seconds_till_hot,
                                                    'ratio_tt': ratio_tt,
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

                with open(f'data/results_routes_{mode}_{city}_jitter{jitter}_ratio_tt{ratio_tt}.pkl', 'wb') as f:
                    pickle.dump(routes, f)

                plot_routes(city, mode, jitter, ratio_tt)

                model.reset_model()
