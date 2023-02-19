from enum import Enum # For Lot class
from functools import reduce # For Workstation class.
import pandas as pd

class Queue:
    # This class represents a generic queue to be used for workstations and truck.

    def __init__(self):
        self.queue = []

    def pop(self, is_lifo = True):
        # Get the first elem of queue
        return self.queue.pop() if is_lifo else self.queue.pop(0)
    
    def add(self, lot):
        # Add lot to the end of list
        self.queue.append(lot)

    def is_empty(self):
        # Check if queue is empty.
        return len(self.queue) == 0
    
class Lot:
    # This class represents a lot.

    class Steps(Enum):
        # This class encapsulates the steps taken by the lot.
        Unstarted = 0
        First = 1
        Second = 2
        Third = 3
        Fourth = 4
        Fifth = 5
        Sixth = 6
        Finished = 7

    def __init__(self, index):
        # Initialise a lot
        self.step = Lot.Steps.First
        self.index = index

    def next(self):
        # Move to next step
        self.step = Lot.Steps(self.step.value + 1)

class Workstation:
    # This class represents a workstation

    class WSQueue(Queue): 
        # The class represents a hypothetical queue.

        def get_time_remaining(self, sp):
            # Returns the remaining time for all tasks in queue.
            get_time = lambda lot: sp[lot.step]
            queue_int = [get_time(lot) for lot in self.queue] # Convert Lot to time.
            return reduce(lambda a, b: a + b, queue_int, 0)

    class CurrentJob:
        # The class represents the current job that the workstation is working on.

        def __init__(self):
            self.lot = None
            self.timer = 0

        def is_finished(self):
            return self.timer == 0 and not self.lot
        
        def add(self, sp, lot):
            self.lot = lot
            self.timer = sp[lot.step]

        def update(self):
            # +1 time
            self.timer = max(0, self.timer - 1)
            if self.timer == 0 and self.lot:
                # Lot just finished.
                temp = self.lot
                self.lot = None
                return temp

        def get_time(self):
            return self.timer

    def __init__(self, spt):
        self.step_process = Workstation.init_step_process(spt)
        self.queue = Workstation.WSQueue()
        self.current_job = Workstation.CurrentJob()

    def init_step_process(spt):
        # Initialise the list of step process time.
        return dict((Lot.Steps(step), time) for step, time in spt)

    def get_time_remaining(self):
        # Obtain the 'hypothetical' time remaining for the next lot's information.
        return self.current_job.get_time() + self.queue.get_time_remaining(self.step_process)
    
    def add_task(self, lot):
        # Add lot to the workstation
        if self.current_job.is_finished():
            # Add lot to current job
            self.current_job.add(self.step_process, lot)
        else:
            # Add lot to hypothetical queue
            self.queue.add(lot)

    def update(self):
        # +1 time
        job = self.current_job.update()
        if self.current_job.is_finished() and not self.queue.is_empty():
            self.current_job.add(self.step_process, self.queue.pop())
        if job:
            return job

class Truck:
    # This class represents a Truck
        
    class Load(Queue):
        # The class represents the load of the truck.
        
        def is_full(self):
            return len(self.queue) >= 5

    def __init__(self, buildings):
        self.load = Truck.Load()
        self.downtime = 0
        self.building = buildings[0]
        self.possible_locations = buildings
    
    def add(self, lot):
        self.load.add(lot)

    def is_full(self):
        return self.load.is_full()

    def move_off(self):
        def swap_buildings():
            for l in self.possible_locations:
                if l is not self.building:
                    return l
        
        self.downtime = 25
        self.building = swap_buildings()

    def update(self):
        if self.downtime == 0:
            while not self.building.truckqueue.is_empty() and not self.is_full():
                self.load.add(self.building.truckqueue.pop())
            if not self.load.is_empty():
                self.move_off()
        else:
            # transporting
            self.downtime = max(0, self.downtime - 1)
            self.building.receive_load(self.load.queue)
            self.load = Truck.Load() # Clear all load

class Building:
    # This class represents a building, which is responsible for accepting truck load & allocating load.

    def __init__(self, all_workstations, my_workstations):
        self.my_workstations = my_workstations
        self.all_workstations = Building.init_workstations(all_workstations)
        self.truckqueue = Queue()

    def init_workstations(workstations):
        # Initialise the list of step and workstation.
        result = {}
        for step, workstation in workstations:
            for w in workstation:
                if Lot.Steps(step) not in result:
                    result[Lot.Steps(step)] = [w]
                else:
                    result[Lot.Steps(step)].append(w)
        return result
        
    def receive_load(self, lots):
        for l in lots:
            possible_workstations = self.all_workstations[l.step]
            times = [(ws.get_time_remaining(), ws) if ws in self.my_workstations else (ws.get_time_remaining()+25, ws) for ws in possible_workstations]
            best_ws = min(times, key = lambda val: val[0])[1]
            if best_ws in self.my_workstations:
                best_ws.add_task(l)
            else:
                self.truckqueue.add(l)

    def update(self):
        # +1 time 
        for ws in self.my_workstations:
            lot = ws.update()
            if lot:
                if lot.step is Lot.Steps.Sixth:
                    return lot
                lot.next()
                self.receive_load([lot])
        
class Micron:

    def __init__(self, buildings, truck, workstations, filename):
        self.start_building = buildings[0]
        self.buildings = buildings
        self.truck = truck
        self.workstations = workstations
        self.filename = filename
    
    def simulate(self, input):
        global finished_list
        self.start_building.receive_load(input)
        finished_counter = 0
        timer = 0
        while finished_counter < len(input):
            self.truck.update()
            for b in self.buildings:
                lot = b.update()
                if lot and lot.step is Lot.Steps.Sixth:
                    finished_list.append(lot.index)
                    finished_counter += 1
            if timer % 5 == 0:
                self.print_output()
            if timer >= 10080:
                return finished_counter
            timer += 1

    def build_input(size):
        result = []
        for i in range(size):
            result.append(Lot(i+1))
        return result

    def print_output(self):
        global final_result

        result = []
        # Print Workstation
        for ws in self.workstations:
            if ws.current_job.lot is None:
                result.append(None)
            else:
                result.append(ws.current_job.lot.index)

        # Print Truck
        for l in self.truck.load.queue:
            result.append(l.index)
        for _ in range(5 - len(self.truck.load.queue)):
            result.append(None)

        # Print Destination
        if self.truck.downtime > 0:
            if self.truck.building == X:
                result.append("X")
            else: 
                result.append("Y")
        else:
            result.append(None)  

        result = []
        # Print Queue
        for ws in self.workstations:
            result.append(len(ws.queue.queue))
        
        for b in self.buildings:
            result.append(len(b.truckqueue.queue))
    
        df = pd.DataFrame(data = [result])
        final_result = pd.concat([final_result, df])
    
# Initialising
A = Workstation([(1,5), (3,10)])
B = Workstation([(2,15), (6,10)])
C = Workstation([(2,15), (5,10)])
D = Workstation([(1,5), (4,15)])
E = Workstation([(1,5), (3,5), (5,15)])
F = Workstation([(4,10), (6,10)])

workstations = [(1, [A]), (2, [B,C]), (3, [A]), (5, [C]), (6, [B]), (1, [D,E]), (3, [E]), (4, [D,F]), (5, [E]), (6, [F])]
X = Building(workstations, [A,B,C])
Y = Building(workstations, [D,E,F])

T = Truck((X,Y))

M = Micron((X,Y), T, (A,B,C,D,E,F), "bacc.csv")

empty = [None,None,None,None,None,None,None,None]#,None,None,None,None]
final_result = pd.DataFrame(data = [empty])

finished_list = []
final_counter = M.simulate(Micron.build_input(500))

# Edit df
#mapping_dict = dict(zip(finished_list, range(1, final_counter+1)))
#last_result = final_result.replace(mapping_dict)
final_result.to_csv("bacc.csv", index = False, header = False)




