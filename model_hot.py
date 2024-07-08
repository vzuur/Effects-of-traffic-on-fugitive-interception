import itertools

import networkx as nx
import numpy as np

from model_elements.entities import Fugitive
from model_elements.intersection_hot import Intersection
from model_elements.road import Road
from model_elements.source_fugitive import SourceFugitive
from pydsol.core.model import DSOLModel
from pydsol.model.entities import Entity
from pydsol.model.server import Server
from pydsol.model.sink import Sink
from pydsol.model.source import Source


class FugitiveModel(DSOLModel):
    def __init__(self, simulator, input_params, seed=None):
        super().__init__(simulator)
        self.seed = seed

        self.input_params = input_params
        self.graph = input_params['graph']
        self.start_fugitive = input_params['start_fugitive']
        self.route_fugitive = input_params['route_fugitive']
        self.num_fugitive_routes = input_params['num_fugitive_routes']
        self.jitter = input_params['jitter']
        self.escape_nodes = input_params['escape_nodes']
        # self.seconds_till_hot = input_params['seconds_till_hot']
        # self.ratio_tt = input_params['ratio_tt']

        # import components and roads
        # self.components = input_params['components']
        # self.roads = input_params['roads']

        # construct graph
        self.components = []
        self.sources = []
        self.source_fugitive = []
        self.roads = []
        self.roads_from_sources = []
        self.construct_nodes()  # construct intersections
        # print('constructed nodes')
        self.construct_links()  # construct roads
        # print('constructed model')

    def construct_nodes(self):
        for node, data in self.graph.nodes(data=True):
            locX = data["x"]
            locY = data["y"]

            component = Intersection(simulator=self.simulator,
                                     location="(" + str(locX) + "," + str(locY) + ")",
                                     name=node,
                                     graph=self.graph,
                                     jitter=self.jitter,
                                     escape_nodes=self.escape_nodes,
                                     # seconds_till_hot=self.seconds_till_hot,
                                     # ratio_tt=self.ratio_tt
                                     )

            self.components.append(component)

    def construct_links(self):
        for i, (u, v, data) in enumerate(self.graph.edges(data=True)):
            origin = next((x for x in self.components if x.name == u), None)
            destination = next((x for x in self.components if x.name == v), None)

            num_lanes = 1
            if 'lanes' in data.keys():
                num_lanes = min(map(int, data['lanes']))

            road = Road(simulator=self.simulator,
                        origin=origin,
                        origin_name=u,
                        destination=destination,
                        destination_name=v,
                        length=data['travel_time'],
                        selection_weight=1,
                        graph=self.graph,
                        maxspeed=data['speed_kph'],
                        numlanes=num_lanes,
                        next=destination
                        )

            self.roads.append(road)

            # TODO ignoring one-way
            road_reverse = Road(simulator=self.simulator,
                                origin=destination,
                                origin_name=v,
                                destination=origin,
                                destination_name=u,
                                length=data['travel_time'],
                                selection_weight=1,
                                graph=self.graph,
                                maxspeed=data['speed_kph'],
                                numlanes=num_lanes,
                                next=origin
                                )

            self.roads.append(road_reverse)

        for node, data in self.graph.nodes(data=True):
            component = next((x for x in self.components if x.name == node), None)
            if type(component) == Intersection:
                component.next = [x for x in self.roads if x.origin == component]

    def construct_sources(self):
        self.sources = []
        self.source_fugitive = []

        # fugitive
        for fug_route in self.route_fugitive:
            route=fug_route
            node = self.start_fugitive
            locX = self.graph.nodes(data=True)[node]["x"]
            locY = self.graph.nodes(data=True)[node]["y"]

            component = SourceFugitive(simulator=self.simulator,
                                       location="(" + str(locX) + "," + str(locY) + ")",
                                       name=node,
                                       interarrival_time=10000000,
                                       num_entities=1,
                                       graph=self.graph,
                                       route=route
                                       )
            self.sources.append(component)
            self.source_fugitive.append(component)

            # ADD EDGES FROM SOURCES TO SOURCE LOCATIONS OF LENGTH 0
            origin = component
            destination = next((x for x in self.components if x.name == self.start_fugitive), None)

            road = Road(simulator=self.simulator,
                        origin=origin,
                        origin_name='Source',
                        destination=destination,
                        destination_name=self.start_fugitive,
                        length=0.001,
                        selection_weight=1,
                        graph=self.graph,
                        maxspeed=0,
                        numlanes=1,
                        next=destination
                        )

            component.next = road
            self.roads_from_sources.append(road)

    def construct_model(self):
        self.reset_model()
        np.random.seed(self.seed)

        self.construct_sources()  # construct sources
        # print('constructed sources')

    def reset_model(self):
        classes = [Source, Sink, Server, Entity, SourceFugitive, Fugitive]  # Road, Intersection,

        for i in classes:
            i.id_iter = itertools.count(1)

    def get_output_statistics(self):
        self.simulator._eventlist.clear()

        for road in self.roads_from_sources:
            del road
        self.roads_from_sources = []

        # delete fugitives and sources
        list_fugitives = []
        for source in self.source_fugitive:
            list_fugitives.append(source.entities_created)
            del source

        fugitive_routes = [fugitive.output_route for fugitive in list_fugitives]
        # num_intercepted = sum([fugitive.intercepted for fugitive in list_fugitives])  # TODO model.num_intercepted
        # pct_intercepted = (num_intercepted / self.num_fugitive_routes) * 100

        del list_fugitives

        # print('pct intercepted: ', pct_intercepted)
        return fugitive_routes

    @staticmethod
    def save(obj):
        return (obj.__class__, obj.__dict__)

    @staticmethod
    def restore(cls, attributes):
        obj = cls.__new__(cls)
        obj.__dict__.update(attributes)
        return obj
