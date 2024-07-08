from pydsol.model.link import Link


class Road(Link):
    def __init__(self, simulator, origin, destination, length, selection_weight=1, **kwargs):
        super().__init__(simulator, origin, destination, length, selection_weight, **kwargs)
        self.graph = kwargs['graph']
        self.destination_name = kwargs["destination_name"]
        self.origin_name = kwargs["origin_name"]
        self.next = kwargs['next']

        if 'maxspeed' in kwargs.keys():  # hot mode
            self.maxspeed = kwargs['maxspeed']
            self.numlanes = kwargs['numlanes']
