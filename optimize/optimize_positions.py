import pickle
import numpy as np
import osmnx as ox
import networkx as nx
from datetime import datetime

from ema_workbench import MultiprocessingEvaluator, SequentialEvaluator
from ema_workbench import RealParameter, ScalarOutcome, Constant, Model
from ema_workbench.em_framework.optimization import ArchiveLogger, SingleObjectiveBorgWithArchive

from sort_and_filter import sort_and_filter_pol_fug_city as sort_and_filter_nodes
#from optimize.unit_ranges import unit_ranges

import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)


def FIP_model(route_fugitive_labeled=None, run_length=None, police_start=None, graph=None, labels_full_sorted=None, labels_sorted=None,
              labels_sorted_inv=None, labels=None,
              **kwargs):
    pi_uv = {}
    z_r = {}
    pi_nodes = {}

    for u, value in enumerate(list(kwargs.values())):
        associated_node = labels_sorted_inv[int(u)][int(np.floor(value))]

        travel_time_to_target = nx.shortest_path_length(graph,
                                                        source=police_start[u],
                                                        target=associated_node,
                                                        weight='police_travel_time') #or police_travel_time_traffic when traffic is included (change manually)
        # TODO: hier politie logica
        associated_node = labels[associated_node]
        pi_nodes[u] = (associated_node, travel_time_to_target)
        # pi_nodes.append(labels_full_sorted[associated_node])

    for i_r, _ in enumerate(route_fugitive_labeled):
        z_r[i_r] = 0

    for i_r, r in enumerate(route_fugitive_labeled):  # for each route
        #if any([node in pi_nodes.values() for node in r.values()]):
        if any ([node in [p[0] for p in pi_nodes.values()] for node in r.values()]):
            for u, pi in pi_nodes.items():  # for each police unit
                for time_at_node_fugitive, node_fugitive in r.items():  # for each node in the fugitive route
                    if node_fugitive == pi[0]:  # if the fugitive node is the same as the target node of the police unit
                        if time_at_node_fugitive > pi[1]:  # and the police unit can reach that node
                            z_r[i_r] = 1  # intercepted

    total_routes = len(route_fugitive_labeled)
    total_intercepted = sum(z_r.values())
    percentage = total_intercepted/total_routes

    # Controleer de berekening en print debug informatie
    #print(f"Total routes: {total_routes}, Total intercepted: {total_intercepted}, Percentage: {percentage}")
    # return [float(sum(z_r.values()))]
    return [float(percentage)]


def get_intercepted_routes(route_fugitive_labeled, police_start, graph, labels_full_sorted, labels_sorted_inv, results_positions):
    z_r = {}
    pi_nodes = {}

    for u, value in enumerate(results_positions):
        associated_node = labels_sorted_inv[int(u)][int(np.floor(value))]
        travel_time_to_target = nx.shortest_path_length(graph,
                                                        source=police_start[u],
                                                        target=associated_node,
                                                        weight='police_travel_time') #or police_travel_time_traffic (anually)
        associated_node = labels_full_sorted[associated_node]
        pi_nodes[u] = (associated_node, travel_time_to_target)

    for i_r, _ in enumerate(route_fugitive_labeled):
        z_r[i_r] = 0

    for i_r, r in enumerate(route_fugitive_labeled):  # for each route
        if any([node in [p[0] for p in pi_nodes.values()] for node in r.values()]):
        #if any([node in pi_nodes.values() for node in r.values()]):
            for u, pi in pi_nodes.items():  # for each police unit
                for time_at_node_fugitive, node_fugitive in r.items():  # for each node in the fugitive route
                    if node_fugitive == pi[0]:  # if the fugitive node is the same as the target node of the police unit
                        if time_at_node_fugitive > pi[1]:  # and the police unit can reach that node
                            z_r[i_r] = 1  # intercepted

    # print(sum(z_r.values())/500)

    # for r in range(len(route_fugitive_labeled)):
    #     z_r[r] = sum(sum(sum(pi_uv[u, v] * phi_rt[r, t, v] * tau_uv[u, t, v] for v in labels_full_sorted.values()) for u in range(U)) for t in range(run_length))

    return z_r


def optimize(G, city, mode, jitter, location, results_routes, police_stations, delays, run_length):
    with open(f'../data/escape_nodes_{city}.pkl', 'rb') as f:
        escape_nodes = pickle.load(f)

    with open(f'../data/fugitive_start_{city}_{location}.pkl', 'rb') as f:
        fugitive_start = pickle.load(f)

    if city != 'Winterswijk':
        with open(f'../data/cameras_{city}.pkl', 'rb') as f:
            cameras = pickle.load(f)
    elif city == 'Winterswijk':
        cameras = []

    # sort indices on distance to start_fugitive
    labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted = sort_and_filter_nodes(G,
                                                                                                 fugitive_start,
                                                                                                 results_routes,
                                                                                                 police_stations,
                                                                                                 run_length)
    print(datetime.now().strftime("%H:%M:%S"),'done constructing labels')
    route_fugitive_labeled = []
    for r in results_routes:
        r_labeled = {x: labels_full_sorted[y] for x, y in r.items()}
        route_fugitive_labeled.append(r_labeled)

    # tau_uv = unit_ranges(start_units=police_stations, delays=delays, U=len(police_stations), G=G, L=run_length,
    #                      labels_full_sorted=labels_full_sorted)
    # print(datetime.now().strftime("%H:%M:%S"),'done constructing unit ranges')

    problem_name = f'{city}_{mode}_jitter{jitter}'

    upper_bounds = []
    for u in range(len(police_stations)):
        if len(labels_perunit_sorted[u]) <= 1:
            upper_bounds.append(0.999)
        else:
            upper_bounds.append(len(labels_perunit_sorted[u]) - 0.001)  # different for each unit
    if any([upper_bounds[i] <= 1 for i in range(len(upper_bounds))]):
        print('ten minste een van je eenheden kan de vluchtroutes niet bereiken')
    model = Model("FIPEMA", function=FIP_model)

    model.levers = [RealParameter(f"pi_{u}", 0, upper_bounds[u]) for u in range(len(police_stations))]

    model.constants = model.constants = [
        Constant("route_fugitive_labeled", route_fugitive_labeled),
        Constant("run_length", run_length),
        Constant("graph", G),
        Constant("police_start", police_stations),
        # Constant("tau_uv", tau_uv),
        Constant("labels_full_sorted", labels_full_sorted),
        Constant("labels", labels_full_sorted),
        Constant("labels_sorted", labels_perunit_sorted),
        Constant("labels_sorted_inv", labels_perunit_inv_sorted)
    ]

    model.outcomes = [
        ScalarOutcome("pct_intercepted", kind=ScalarOutcome.MAXIMIZE)
    ]

    print(datetime.now().strftime("%H:%M:%S"), 'starting optimization')
    highest_perf = 0
    with MultiprocessingEvaluator(model) as evaluator:
        for _ in range(1):
            convergence_metrics = [
                ArchiveLogger(
                    f"../results/optimization/",
                    [l.name for l in model.levers],
                    [o.name for o in model.outcomes if o.kind != o.INFO],
                    base_filename=f"archives_{city}_{mode}_{jitter}.tar.gz"
                ),
            ]

            result = evaluator.optimize(
                algorithm=SingleObjectiveBorgWithArchive,
                nfe=5000,
                searchover="levers",
                convergence=convergence_metrics,
                convergence_freq=100
            )

            result = result.iloc[0]
            if result['pct_intercepted'] >= highest_perf:
                results = result

    results_positions = []
    results_positions_labeled = []
    for u, start in enumerate(police_stations):
        results_positions.append(results[f'pi_{u}'])
        results_positions_labeled.append(labels_perunit_inv_sorted[u][int(np.floor(results[f'pi_{u}']))])
    # print(results_positions)

    routes_intercepted = get_intercepted_routes(route_fugitive_labeled,
                                                police_stations,
                                                G,
                                                labels_full_sorted,
                                                labels_perunit_inv_sorted,
                                                results_positions
                                                )
    # print(routes_intercepted)

    return results, routes_intercepted, results_positions_labeled


if __name__ == '__main__':
    run_length = 1800

    # mode = 'cool'
    # for city in ['Rotterdam']:
    #     for jitter in [0.02]:
    #         for location in ['centre', 'port']:
    #             for number_units in ['2','4']:
    #                 print(location,number_units)
    #                 for traffic in ['withouttraffic']: #or withtraffic (change manually)
    #                     filepath = f"../graphs/{city}_{traffic}_prepped.graph.graphml"
    #                     G = ox.load_graphml(filepath=filepath)
    #
    #                     travel_time_dict = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         travel_time_dict[(u, v, k)] = float(data['travel_time_adj'])
    #
    #                     nx.set_edge_attributes(G, travel_time_dict, "travel_time_adj")
    #
    #                     congestion_travel_time_dict = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         congestion_travel_time_dict[(u, v, k)] = float(data['travel_time_with_congestion'])
    #
    #                     nx.set_edge_attributes(G, congestion_travel_time_dict, "travel_time_with_congestion")
    #
    #                     police_travel_time_dict = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         police_travel_time_dict[(u, v, k)] = float(data['police_travel_time'])
    #
    #                     nx.set_edge_attributes(G, police_travel_time_dict, "police_travel_time")
    #
    #                     police_travel_time_dict_traffic = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         police_travel_time_dict_traffic[(u, v, k)] = float(data['police_travel_time_traffic'])
    #
    #                     nx.set_edge_attributes(G, police_travel_time_dict_traffic, "police_travel_time_traffic")
    #
    #                     with open(f'../data/optimization/start_police_{city}_{number_units}.pkl', 'rb') as f:
    #                         police_stations = pickle.load(f)
    #                        # print(police_stations)
    #
    #                     with open(f'../data/optimization/delays_police_{city}_{number_units}.pkl', 'rb') as f:
    #                         delays = pickle.load(f)
    #
    #                     # import results
    #                     with open(f'../data/results_routes_{mode}_{city}_jitter{jitter}_{location}_{traffic}.pkl', 'rb') as f:
    #                         results_routes = pickle.load(f)
    #
    #                     results, intercepted_routes, results_positions = optimize(G, city, mode, jitter, location, results_routes, police_stations, delays, run_length)
    #                     print(results)
    #
    #                     with open(f'../results/optimization/results_optimization_{mode}_{city}_jitter{jitter}_{location}_{number_units}_{traffic}.pkl', 'wb') as f:
    #                         pickle.dump(results, f)
    #
    #                     with open(f'../results/optimization/results_intercepted_routes_{mode}_{city}_jitter{jitter}_{location}_{number_units}_{traffic}.pkl', 'wb') as f:
    #                         pickle.dump(intercepted_routes, f)
    #
    #                     with open(f'../results/optimization/results_positions_{mode}_{city}_jitter{jitter}_{location}_{number_units}_{traffic}.pkl', 'wb') as f:
    #                         pickle.dump(results_positions, f)
    #
    #                     print(mode, city, jitter, location, number_units, traffic)
    #                     pct_intercepted = results['pct_intercepted']
    #
    #
    # mode = 'hot'
    # for city in ['Rotterdam']:
    #     for jitter in [0.02]:
    #         for location in ['port','centre']:
    #             for number_units in ['2','4']:
    #                 for traffic in ['withouttraffic']: # or 'withtraffic' (change manually)
    #                     filepath = f"../graphs/{city}_{traffic}_prepped.graph.graphml"
    #                     G = ox.load_graphml(filepath=filepath)
    #
    #                     with open(f'../data/optimization/start_police_{city}_{number_units}.pkl', 'rb') as f:
    #                         police_stations = pickle.load(f)
    #
    #                     with open(f'../data/optimization/delays_police_{city}_{number_units}.pkl', 'rb') as f:
    #                         delays = pickle.load(f)
    #
    #                     travel_time_dict = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         travel_time_dict[(u, v, k)] = float(data['travel_time_adj'])
    #
    #                     nx.set_edge_attributes(G, travel_time_dict, "travel_time_adj")
    #
    #                     congestion_travel_time_dict = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         congestion_travel_time_dict[(u, v, k)] = float(data['travel_time_with_congestion'])
    #
    #                     nx.set_edge_attributes(G, congestion_travel_time_dict, "travel_time_with_congestion")
    #
    #                     police_travel_time_dict = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         police_travel_time_dict[(u, v, k)] = float(data['police_travel_time'])
    #
    #                     nx.set_edge_attributes(G, police_travel_time_dict, "police_travel_time")
    #
    #                     police_travel_time_dict_traffic = {}
    #                     for u, v, k, data in G.edges(data=True, keys=True):
    #                         police_travel_time_dict_traffic[(u, v, k)] = float(data['police_travel_time_traffic'])
    #
    #                     nx.set_edge_attributes(G, police_travel_time_dict_traffic, "police_travel_time_traffic")
    #
    #                     # import results
    #                     with open(f'../data/results_routes_{mode}_{city}_jitter{jitter}_{location}_{traffic}.pkl', 'rb') as f:
    #                         results_routes = pickle.load(f)
    #
    #                     results, intercepted_routes, results_positions = optimize(G, city, mode, jitter, location, results_routes, police_stations, delays, run_length)
    #                     print(results)
    #
    #
    #                     with open(f'../results/optimization/results_optimization_{mode}_{city}_jitter{jitter}_{location}_{number_units}_{traffic}.pkl', 'wb') as f:
    #                         pickle.dump(results, f)
    #
    #                     with open(f'../results/optimization/results_intercepted_routes_{mode}_{city}_jitter{jitter}_{location}_{number_units}_{traffic}.pkl', 'wb') as f:
    #                         pickle.dump(intercepted_routes, f)
    #
    #                     with open(f'../results/optimization/results_positions_{mode}_{city}_jitter{jitter}_{location}_{number_units}_{traffic}.pkl', 'wb') as f:
    #                         pickle.dump(results_positions, f)
    #
    #                     print(mode, city, jitter, location, number_units)
    #                     pct_intercepted = results['pct_intercepted']


    mode = 'hot+cool'
    for jitter in [0.02]:
        for city in ['Rotterdam']:
            for location in ['port', 'centre']:
                for number_units in ['2', '4']:
                    for traffic in ['withouttraffic']: #or 'withtraffic' (change manually)
                        results_routes = []
                        filepath = f"../graphs/{city}_{traffic}_prepped.graph.graphml"
                        G = ox.load_graphml(filepath=filepath)
                        # filepath = f"graphs/{city}.graph.graphml"
                        # G = ox.load_graphml(filepath=filepath)

                        with open(f'../data/optimization/start_police_{city}_{number_units}.pkl', 'rb') as f:
                            police_stations = pickle.load(f)

                        with open(f'../data/optimization/delays_police_{city}_{number_units}.pkl', 'rb') as f:
                            delays = pickle.load(f)

                        travel_time_dict = {}
                        for u, v, k, data in G.edges(data=True, keys=True):
                            travel_time_dict[(u, v, k)] = float(data['travel_time_adj'])

                        nx.set_edge_attributes(G, travel_time_dict, "travel_time_adj")

                        congestion_travel_time_dict = {}
                        for u, v, k, data in G.edges(data=True, keys=True):
                            congestion_travel_time_dict[(u, v, k)] = float(data['travel_time_with_congestion'])

                        nx.set_edge_attributes(G, congestion_travel_time_dict, "travel_time_with_congestion")

                        police_travel_time_dict = {}
                        for u, v, k, data in G.edges(data=True, keys=True):
                            police_travel_time_dict[(u, v, k)] = float(data['police_travel_time'])

                        nx.set_edge_attributes(G, police_travel_time_dict, "police_travel_time")

                        police_travel_time_dict_traffic = {}
                        for u, v, k, data in G.edges(data=True, keys=True):
                            police_travel_time_dict_traffic[(u, v, k)] = float(data['police_travel_time_traffic'])

                        nx.set_edge_attributes(G, police_travel_time_dict_traffic, "police_travel_time_traffic")

                        # import results
                        with open(f'../data/results_routes_hot_{city}_jitter{0.02}_{location}_{traffic}.pkl', 'rb') as f:
                            results_routes_hot = pickle.load(f)
                            results_routes += results_routes_hot
                        # with open(f'../data/results_routes_hot_{city}_jitter{0.2}_{location}_{traffic}.pkl', 'rb') as f:
                        #     results_routes_hot = pickle.load(f)
                        #     results_routes += results_routes_hot
                        with open(f'../data/results_routes_cool_{city}_jitter{0.02}_{location}_{traffic}.pkl', 'rb') as f:
                            results_routes_cool = pickle.load(f)
                            results_routes += results_routes_cool
                        # with open(f'../data/results_routes_cool_{city}_jitter{0.02}.pkl', 'rb') as f:
                        #     results_routes_cool = pickle.load(f)
                        #     results_routes += results_routes_cool

                        results, intercepted_routes, results_positions = optimize(G, city, mode, jitter, location, results_routes, police_stations, delays, run_length)
                        print(results)

                        with open(f'../results/optimization/results_optimization_{mode}_{city}_jitter{jitter}_{location}_{traffic}.pkl', 'wb') as f:
                            pickle.dump(results, f)

                        with open(f'../results/optimization/results_intercepted_routes_{mode}_{city}_jitter{jitter}_{location}_{traffic}.pkl', 'wb') as f:
                            pickle.dump(intercepted_routes, f)

                        with open(f'../results/optimization/results_positions_{mode}_{city}_jitter{jitter}_{location}_{traffic}.pkl', 'wb') as f:
                            pickle.dump(results_positions, f)

                        print(mode, city, jitter, location, number_units, traffic)
                        pct_intercepted = results['pct_intercepted']





