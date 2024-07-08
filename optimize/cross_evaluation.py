import pickle
import numpy as np
import osmnx as ox
import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt

import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
from sort_and_filter import sort_and_filter_pol_fug_city as sort_and_filter_nodes

iteration_dicts = [
    #hot and cool for the center location with 2 units
    {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '2', 'traffic': 'withouttraffic'},
    {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '2', 'traffic': 'withtraffic'},
    {'mode': 'hot', 'jitter': 0.02, 'location': 'centre', 'number_units': '2', 'traffic': 'withouttraffic'},
    {'mode': 'hot', 'jitter': 0.02, 'location': 'centre', 'number_units': '2', 'traffic': 'withtraffic'},

    # #hot and cool for the port location with 2 units
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'port', 'number_units': '2', 'traffic': 'withouttraffic'},
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'port', 'number_units': '2', 'traffic': 'withtraffic'},
    # {'mode': 'hot', 'jitter': 0.02, 'location': 'port', 'number_units': '2', 'traffic': 'withouttraffic'},
    # {'mode': 'hot', 'jitter': 0.02, 'location': 'port', 'number_units': '2', 'traffic': 'withtraffic'},

    #hot and cool for the center location with 4 units
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'withouttraffic'},
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'withtraffic'},
    # {'mode': 'hot', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'withouttraffic'},
    # {'mode': 'hot', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'withtraffic'},

    # #hot and cool for the port location with 4 units
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'port', 'number_units': '4', 'traffic': 'withouttraffic'},
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'port', 'number_units': '4', 'traffic': 'withtraffic'},
    # {'mode': 'hot', 'jitter': 0.02, 'location': 'port', 'number_units': '4', 'traffic': 'withouttraffic'},
    # {'mode': 'hot', 'jitter': 0.02, 'location': 'port', 'number_units': '4', 'traffic': 'withtraffic'},

    # #cool for the center location with 2 units with all combinations of traffic
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'withouttraffic'},
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'withtraffic'},
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'onlycongestion'},
    # {'mode': 'cool', 'jitter': 0.02, 'location': 'centre', 'number_units': '4', 'traffic': 'onlytrafficlights'},
]

labels = [
    'cool, center, 2, withouttraffic',
    'cool, center, 2, withtraffic',
    'hot, center, 2, withouttraffic',
    'hot, center, 2, withtraffic',

    # 'cool, port, 2, withouttraffic',
    # 'cool, port, 2, withtraffic',
    # 'hot, port, 2, withouttraffic',
    # 'hot, port, 2, withtraffic',

    # 'cool, center, 4, withouttraffic',
    # 'cool, center, 4, withtraffic',
    # 'hot, center, 4, withouttraffic',
    # 'hot, center, 4, withtraffic',

    # 'cool, port, 4, withouttraffic',
    # 'cool, port, 4, withtraffic',
    # 'hot, port, 4, withouttraffic',
    # 'hot, port, 4, withtraffic',

    # 'cool, center, 4, withouttraffic',
    # 'cool, center, 4, withtraffic',
    # 'cool, center, 4, onlycongestion',
    # 'cool, center, 4, onlytrafficlights',
]

city = 'Rotterdam'
filepath = f"../graphs/{city}.graph.graphml"
G = ox.load_graphml(filepath=filepath)

# def get_intercepted_routes(route_fugitive, results_positions):
#     z_r = {}
#     pi_nodes = {}
#
#     for u, value in enumerate(results_positions):
#         pi_nodes[u] = value  # results_positions[u] wordt de waarde voor sleutel u
#
#     for i_r, _ in enumerate(route_fugitive):
#         z_r[i_r] = 0
#
#     for i_r, r in enumerate(route_fugitive):  # voor elke route
#         if any(node in pi_nodes.values() for node in r.values()):  # controleer of een node in pi_nodes aanwezig is
#             for u, pi in pi_nodes.items():  # voor elke politie-eenheid
#                 for time_at_node_fugitive, node_fugitive in r.items():  # voor elke node in de vluchtroute
#                     if node_fugitive == pi:  # als de vluchtnode dezelfde is als de target node van de politie-eenheid
#                         if time_at_node_fugitive > 0:  # aangenomen dat tijd altijd groter is dan 0
#                             z_r[i_r] = 1  # onderschept
#     return float(sum(z_r.values()))

def get_intercepted_routes(route_fugitive_labeled, police_start, graph, labels_full_sorted, labels_sorted_inv, results_positions):
    z_r = {}
    pi_nodes = {}

    for u, value in enumerate(results_positions):
        associated_node = value
        travel_time_to_target = nx.shortest_path_length(graph,
                                                        source=police_start[u],
                                                        target=associated_node,
                                                        weight='police_travel_time_eval') #gemiddelde snelheid gebruikt voor politie mét en zonder congestie om het eerlijk te houden
        pi_nodes[u] = (associated_node, travel_time_to_target)

    for i_r, _ in enumerate(route_fugitive_labeled):
        z_r[i_r] = 0

    for i_r, r in enumerate(route_fugitive_labeled):  # for each route
        if any([node in [p[0] for p in pi_nodes.values()] for node in r.values()]):
            for u, pi in pi_nodes.items():  # for each police unit
                for time_at_node_fugitive, node_fugitive in r.items():  # for each node in the fugitive route
                    if node_fugitive == pi[0]:  # if the fugitive node is the same as the target node of the police unit
                        if time_at_node_fugitive > pi[1]:  # and the police unit can reach that node
                            z_r[i_r] = 1  # intercepted

    return float(sum(z_r.values())) #return z_r stond er eerst

def get_scores():
    scores = np.zeros((len(iteration_dicts), len(iteration_dicts)))

    for j in range(len(iteration_dicts)):
        for i in range(len(iteration_dicts)):
            mode_opt = iteration_dicts[i]['mode']
            jitter_opt = iteration_dicts[i]['jitter']
            location_opt = iteration_dicts[i]['location']
            number_units_opt = iteration_dicts[i]['number_units']
            traffic_opt = iteration_dicts[i]['traffic']
            mode_eval = iteration_dicts[j]['mode']
            jitter_eval = iteration_dicts[j]['jitter']
            location_eval = iteration_dicts[j]['location']
            number_units_eval = iteration_dicts[j]['number_units']
            traffic_eval = iteration_dicts[j]['traffic']

            if mode_eval == 'hot+cool':
                results_routes = []
                with open(f'../data/results_routes_hot_{city}_jitter{0.05}.pkl', 'rb') as f:
                    results_routes_hot = pickle.load(f)
                    results_routes += results_routes_hot
                with open(f'../data/results_routes_hot_{city}_jitter{0.1}.pkl', 'rb') as f:
                    results_routes_hot = pickle.load(f)
                    results_routes += results_routes_hot
                with open(f'../data/results_routes_cool_{city}_jitter{0.02}.pkl', 'rb') as f:
                    results_routes_cool = pickle.load(f)
                    results_routes += results_routes_cool
                with open(f'../data/results_routes_cool_{city}_jitter{0.05}.pkl', 'rb') as f:
                    results_routes_cool = pickle.load(f)
                    results_routes += results_routes_cool
            else:
                with open(f'../data/results_routes_{mode_eval}_{city}_jitter{jitter_eval}_{location_eval}_{traffic_eval}.pkl', 'rb') as f:
                    results_routes = pickle.load(f)

            with open(f'../data/optimization/start_police_{city}_{number_units_eval}.pkl', 'rb') as f:
                police_start = pickle.load(f)
            with open(f'../data/optimization/delays_police_{city}_{number_units_eval}.pkl', 'rb') as f:
                delays = pickle.load(f)
            if mode_opt == 'hot+cool':
                with open(f'../results/optimization/results_positions_{mode_opt}_{city}_{location_opt}_{number_units_opt}.pkl', 'rb') as f:
                    police_end = pickle.load(f)
            else:
                with open(f'../results/optimization/results_positions_{mode_opt}_{city}_jitter{jitter_opt}_{location_opt}_{number_units_opt}_{traffic_opt}.pkl', 'rb') as f:
                    police_end = pickle.load(f)

            labels_perunit_sorted, labels_perunit_inv_sorted, labels_full_sorted = sort_and_filter_nodes(
                G, [list(route.values()) for route in results_routes][0][0],
                results_routes, police_start, 1800)

            score = get_intercepted_routes(
                results_routes, police_start, G, labels_full_sorted, labels_perunit_inv_sorted, police_end)
            if mode_eval == 'hot+cool':
                score = score / 4
            print(score)
            scores[i][j] = score

    with open(f'../results/optimization/scores_{city}_{location_eval}_{number_units_eval}.pkl', 'wb') as f:
        pickle.dump(scores, f)

    for i in range(len(iteration_dicts)):
        row = scores[i]
        diag = scores[i][i]
        scores[i] = (scores[i] - diag) / diag
    with open(f'../results/optimization/normalisedscores_{city}_{location_eval}_{number_units_eval}.pkl', 'wb') as f:
        pickle.dump(scores, f)

    cmap = sns.diverging_palette(0, 255, sep=20, as_cmap=True)
    sns.heatmap(scores, vmin=-1, vmax=1, cmap=cmap, center=0, annot=True, fmt=".2f", xticklabels=labels, yticklabels=labels, linewidths=0.05, cbar=False)
    plt.ylabel('Optimization model')
    plt.xlabel('Evaluation model')
    plt.savefig(f'../results/optimization/heatmap_{city}_{location_eval}_{number_units_eval}_divpalette.png', bbox_inches='tight', dpi=300)

get_scores()