import math
import random
import networkx as nx

import logging
from basic_logger import get_module_logger
logger = get_module_logger(__name__, level=logging.INFO)

from pydsol.model.node import Node
from model_elements.entities import Fugitive


class Intersection(Node):
    def __init__(self, simulator, capacity=math.inf, **kwargs):
        super().__init__(simulator, **kwargs)
        self.location = kwargs['location']
        self.graph = kwargs['graph']
        self.simulator = simulator
        self.jitter = kwargs['jitter']
        self.escape_nodes = kwargs['escape_nodes']
        # self.route = kwargs['route']
        self.next = None


    def enter_input_node(self, entity, **kwargs):
        super().enter_input_node(entity, **kwargs)
        logger.debug(f"Time {self.simulator.simulator_time:.2f}: Entity: {entity.name} entered node{self.name}")

        #save route
        entity.output_route[self.simulator.simulator_time] = self.name


    def exit_output_node(self, entity, **kwargs):
        assert self.name == entity.route_planned[0]

        if len(entity.route_planned) <= 1:  # reached destination node
            logger.debug(f"Time {self.simulator.simulator_time:.2f}: {entity.name} has reached destination node {self.name}")
            pass

        elif self.name in self.escape_nodes:  # reached escape node
            logger.debug(f"Time {self.simulator.simulator_time:.2f}: {entity.name} has reached escape node {self.name}")
            pass


        elif self.name == entity.route_planned[1]:  # next node is the current node; i.e., posting
            entity.route_planned.pop(0)
            self.simulator.schedule_event_rel(1, self, "enter_input_node", entity=entity)

            if type(entity) == Fugitive:
                logger.debug(f"Time {self.simulator.simulator_time:.2f}: {entity.name} is posting at node {self.name}")
                pass
            else:
                pass

        else:
            try:
                entity.route_planned.pop(0)  # remove current node from planned route
                neighbors = [link.destination_name for link in self.next]
                neighbors = [neighbor for neighbor in neighbors if nx.has_path(self.graph, neighbor, entity.escape_node)]
                if len(neighbors) > 1:
                    if random.random() >= self.jitter:
                        next_node = entity.route_planned[0]

                    else:
                        # next_node = random choice of neighboring nodes excl entity.route_planned[0]
                        neighbors.remove(entity.route_planned[0])
                        next_node = random.choice(neighbors)
                        entity.route_planned = nx.shortest_path(self.graph, next_node, entity.escape_node, 'travel_time_adj')

                        #make u-turns less likely after going the wrong way
                        # change link travel_time_adj of opposite link to high
                        for u, v in self.graph.in_edges(self.name):
                            self.graph[u][v][0]['travel_time_adj'] += 20

                else:
                    next_node = entity.route_planned[0]

                for link in self.next:
                    if link.destination_name == next_node:
                        destination_link = link
                        destination_link.enter_link(entity)

                        logger.debug("Time {0:.2f}: Entity: {1} exited node{2}".format(self.simulator.simulator_time,
                                                                                      entity.name, self.name))
                        break

                if 'destination_link' not in locals():
                    raise Exception(f'The destination node {next_node} of {entity.name} is not an output link of the current node {self.name}')

                #del destination_link

            except AttributeError:
                raise AttributeError(f"{self.name} has no output link")






