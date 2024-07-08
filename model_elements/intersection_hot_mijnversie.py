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
        self.traffic_lights = kwargs['traffic_lights']
        self.traffic_light_categories = kwargs['traffic_light_categories']
        self.traffic_light_configuration = kwargs['traffic_light_configuration']
        self.cross_green_wave_road = kwargs['cross_green_wave_road']
        self.green_wave_road = kwargs['green_wave_road']
        self.nodes_onvoorzieneomstandigheid = kwargs['nodes_onvoorzieneomstandigheid']
        self.roundabouts = kwargs['roundabouts']


    def enter_input_node(self, entity, **kwargs):
        super().enter_input_node(entity, **kwargs)
        logger.debug(f"Time {self.simulator.simulator_time:.2f}: Entity: {entity.name} entered node{self.name}")

        #save route
        entity.output_route[self.simulator.simulator_time] = self.name

    def get_wait_time(self, cycle_time=60, green_time=15, threshold =30):
        # Trek een random moment van aankomen binnen de cyclus
        random_time = random.uniform(0, cycle_time)
        if random_time <= green_time:
            # Binnen de groentijd aankomen levert een wachttijd op van 0 seconden
            wait_time = 0
        else:
            # Als je binnen de roodtijd aankomt is de wachttijd de resterende tijd tot het einde van de roodtijd
            wait_time = cycle_time - random_time
        return wait_time

    # def get_wait_time(self, entity, cycle_time=60, green_time=15, threshold=30, num_lanes=3):
    #     # prev_edge = (list(entity.output_route.values())[-2], list(entity.output_route.values())[-1])
    #     # num_lanes = self.graph.get_edge_data(prev_edge[0], prev_edge[1])['num_lanes']
    #     # if isinstance(num_lanes, list):
    #     #     num_lanes = num_lanes[-1]
    #     max_attempts = min(num_lanes - 1, 2)  # Maximaal 2 extra pogingen (wat voorkomt als er 3 richtingen zijn van een verkeerslicht)
    #     first_wait_time = None
    #     for attempt in range(max_attempts + 1):  # één initiële poging, en afhankelijk van het aantal banen nog extra optie(s)
    #         # Trek een random moment van aankomen binnen de cyclus
    #         random_time = random.uniform(0, cycle_time)
    #         if random_time <= green_time:
    #             # Binnen de groentijd aankomen levert een wachttijd op van 0 seconden
    #             wait_time = 0
    #         else:
    #             # Als je binnen de roodtijd aankomt is de wachttijd de resterende tijd tot het einde van de roodtijd
    #             wait_time = cycle_time - random_time
    #         # maar iemand in hot mode wil niet te lang wachten, dus gaat proberen een andere richting te vinden die sneller groen wordt
    #         if first_wait_time is None:
    #             first_wait_time = wait_time
    #         # Controleer of de wachttijd onder de threshold value ligt
    #         if wait_time <= threshold:
    #             return wait_time
    #     # Als geen van de wachttijden onder de drempelwaarde ligt, return de eerste wachttijd (dan volgen ze toch de bedachte route)
    #     return first_wait_time

    def green_wave_calculation(self, entity):
        # return self.get_wait_time(60,60)
        if (self.name, entity.route_planned[0]) in self.green_wave_road:
            #omdat de groene golf in blokken van 5 verkeerslichten wordt geregeld is er bij 4 van de 5 groene golf verkeerslichten een wachttijd van 0, en anders een normale wachttijd
            if random.random() < 0.8:
                wait_time = 0
                return wait_time
            else:
                return self.get_wait_time(60,20)
        else:
            return self.get_wait_time(60,15) #zelfde cyclustijd als bovenstaande ^, maar een kortere groentijd voor de kruisende wegen van de groene golf

    def get_processing_time(self,entity):
        if self.name in self.traffic_lights:
            category = self.traffic_light_categories.get(self.name)
            if category in self.traffic_light_configuration:
                config = self.traffic_light_configuration[category]
                cycle_time = config['cycle_time']
                green_time = config['green_time']
                #print(f"Cycle Time: {cycle_time}, Green Time: {green_time}")
            else:
                return self.get_wait_time()  # Default wait time if category is not found

            if category == 'green_wave':
                # print('green wave')
                return self.green_wave_calculation(entity)
            elif category == 'intersection_with_tram':
                return self.get_wait_time(cycle_time, green_time)
            elif category == 'default':
                return self.get_wait_time(cycle_time, green_time)
        # voor de wachttijd voor een rotonde is gekozen voor 15 seconden (met 80% gebruik van de capaciteit van een weg tijdens de file)
        #elif self.name in self.roundabouts:
            #return 7 #15 seconden per rotonde, ervanuit gaande dat er 2 nodes zijn waar iemand langskomt op een rotonde
        else:
            return 0

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
                processing_time = self.get_processing_time(entity)
                if self.name in self.traffic_lights:
                    original_route_planned = entity.route_planned[:]
                    if len(neighbors) > 1:
                        if processing_time <= 40: # als de wachttijd acceptabel is blijft men de geplande route volgen
                            next_node = entity.route_planned[0] #dan wil je de geplande route blijven volgen

                        else:
                            # ga afwijken van geplande route
                            # while len(neighbors) > 1:
                            #     if processing_time > 40: #40 = threshold want zoveel seconden is het maximaal waard om om te rijden bij een verkeerslicht
                            neighbors.remove(entity.route_planned[0])
                            next_node = random.choice(neighbors)
                            entity.route_planned = nx.shortest_path(self.graph, next_node, entity.escape_node,
                                                                            'travel_time_adj')
                            processing_time = self.get_processing_time(entity)
                            #print('de eerste keer afwijken', processing_time)
                            if processing_time > 40 and len(neighbors) > 1:
                                neighbors.remove(entity.route_planned[0])
                                next_node = random.choice(neighbors)
                                entity.route_planned = nx.shortest_path(self.graph, next_node, entity.escape_node,
                                                                        'travel_time_adj')
                                processing_time = self.get_processing_time(entity)
                                #print('de tweede keer afwijken', processing_time)
                                if processing_time > 40 and len(neighbors)> 1:
                                    neighbors.remove(entity.route_planned[0])
                                    next_node = random.choice(neighbors)
                                    entity.route_planned = nx.shortest_path(self.graph, next_node, entity.escape_node,
                                                                            'travel_time_adj')
                                    processing_time = self.get_processing_time(entity)
                                    #print('de derde keer afwijken', processing_time)
                                    if processing_time > 40:
                                        entity.route_planned = original_route_planned
                                        next_node = entity.route_planned[0]
                                        #print('toch terugvallen op initiële route', processing_time)




                    else:
                        next_node = entity.route_planned[0]

                    for link in self.next:
                        if link.destination_name == next_node:
                            destination_link = link
                            #processing_time = self.get_processing_time(entity)
                            # Hier: if processing_time > threshold(?) AND num_lanes > 2:
                            # delete vorige next_node uit neighbors
                            # pak andere node uit neighbors
                            # doe weer for link in self.next, link.destination_name == next_node etc (max 2 keer nesten)
                            # bepaal processing_time van de nieuwe next_node
                            # else enter link
                            # Hier: if processing_time > threshold(?) AND num_lanes > 3:
                            # else enter link

                            destination_link.enter_link(entity, processing_time)

                            logger.debug(
                                "Time {0:.2f}: Entity: {1} exited node{2}".format(self.simulator.simulator_time,
                                                                                  entity.name, self.name))
                            break
                else:
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
                            processing_time = self.get_processing_time(entity)
                            destination_link.enter_link(entity, processing_time)

                            logger.debug("Time {0:.2f}: Entity: {1} exited node{2}".format(self.simulator.simulator_time,
                                                                                          entity.name, self.name))
                            break

                if 'destination_link' not in locals():
                    raise Exception(f'The destination node {next_node} of {entity.name} is not an output link of the current node {self.name}')

                #del destination_link

            except AttributeError:
                raise AttributeError(f"{self.name} has no output link")






