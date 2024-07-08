from pydsol.model.link import Link
import pickle

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

    def enter_link(self, entity, processing_time=0,  **kwargs):
        """Determines the time for travelling on the link by length and speed of the entity, and
        schedules the event for exiting the link.

        Parameters
        ----------
        entity: object
            the target on which a state change is scheduled.
        kwargs:
            kwargs are the keyword arguments that are used to expand the link class.

        """
        wait_time_list_cool = []
        if processing_time != 0:
            print(processing_time)
        #     wait_time_list_cool.append(processing_time)
        #
        # with open(f'./results/wait_time_list_cool.pkl', 'wb') as f:
        #     pickle.dump(wait_time_list_cool, f)

        relative_delay = self.length/entity.speed + processing_time

        self.simulator.schedule_event_rel(relative_delay, self, "exit_link", entity=entity)

        # logger.debug("Time {0:.2f}: {1} enters {2} from {3} to {4}".format(self.simulator.simulator_time,
        #                                                                               entity.name, self.name,
        #                                                                     self.origin.name, self.destination.name))
