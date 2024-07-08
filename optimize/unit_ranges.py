import networkx as nx
import numpy as np
import pandas as pd
import random

#def police_travel_time(G, u, v, z, data):
 #   for u, v, z, data in G.edges(data=True, keys=True):
  #      return (data['travel_time']/2)

   #  politie rijdt 20% harder dan de maximale snelheid
 #  for u, v,z, data in G.edges(data=True,keys=true):
  #     police_travel_time = data['travel_time'] * 0,5
  #     data['police_travel_time'] = police_travel_time
  #  police_travel_time_dict = {}
   #    police_travel_time = 2
    #    police_travel_time_dict[(u, v, z)] = float(police_travel_time)
    #nx.set_edge_attributes(G, police_travel_time_dict, "police_travel_time")

def unit_ranges(start_units, delays, U, G, L, labels_full_sorted):
    # units_range_index = pd.MultiIndex.from_product(
    #     [range(U), range(L), labels.values()], names=("unit", "time", "node")
    # )
    # units_range_time = pd.DataFrame(index=units_range_index, columns=["inrange"])

    units_range_index = pd.MultiIndex.from_product(
        [range(U), range(len(labels_full_sorted))], names=("unit", "vertex")
    )
    units_range_time = pd.DataFrame(index=units_range_index, columns=["time_to_reach"])

    for u in range(U):
        for v in labels_full_sorted:
            # neighbors = list(
            #     nx.single_source_shortest_path_length(
            #         G, source=start_units[u], cutoff=t
            #     ).keys()
            # )
            # for neighbor in neighbors:
            #     if (
            #         neighbor in labels.keys()
            #     ):  # anders niet in range van fugitive, en dus geen goede target node
            #         units_range_time.loc[(u, t, labels[neighbor])]["inrange"] = 1

            if nx.has_path(G, start_units[u], v):
                # delay = vertraging van buiten de map beginnen
                units_range_time.loc[(u, labels_full_sorted[v])] = nx.shortest_path_length(G,
                                                                                           source=start_units[u],
                                                                                           target=v,
                                                                                           weight='police_travel_time',
                                                                                           method='bellman-ford') + delays[u]
                # print(units_range_time)
            else:
                units_range_time.loc[(u, labels_full_sorted[v])] = 424242

    units_range_time = units_range_time.fillna(0)

    return np.squeeze(units_range_time).to_dict()




