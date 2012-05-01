'''
Created on April 27, 2012
@author: Jonathan Kowalski

Class for Controller

'''
from elevator import Elevator
import Queue
import threading
import logging
import time
logging.basicConfig(filename='elevator.log',level=logging.DEBUG)


class Controller(threading.Thread):


    def __init__(self, num_elevators, num_floors):
        # the elevator are numbered from 0 to num_elevators-1
        self.num_elevators = num_elevators
        # the floors are numbered from 0 to num_floors-1
        self.num_floors = num_floors
        # the elevator objects are saved in a dictionary keyed by their number
        self.elevators = dict()

        self.queue = Queue.Queue()

        for i in range(self.num_elevators):
             e = Elevator(self.num_floors)
             e.setName(i)
             # the elevators are threaded
             e.start()
             self.elevators[i] = e

        threading.Thread.__init__(self)

    def optimize(self):
        # For the case where if an elevator becomes WAITING and it is in closer range of a control request
        # allow the elevator to intercept that request as long as the current elevator has no user requests closer
        # than the distance that the WAITING elevator currently resides.

        # waiting elevators are elevators that are not currently servicing any requests.
        waiting_elevators = []
        # working elevators are elevators that are currently servicing a set of requests.
        working_elevators = []
        for i in self.elevators:
            if self.elevators[i].status == Elevator.WAITING and not self.elevators[i].crash:
                waiting_elevators.append(self.elevators[i])
            elif not self.elevators[i].crash:
                working_elevators.append(self.elevators[i])

        if waiting_elevators:
            for working_e in working_elevators:
                best_elevator = None
                # first we determine the direction of the elevator and distance from request
                if working_e.status == Elevator.MOVING_UP:
                    distance_from_called = working_e.called_floor - working_e.current_floor
                elif working_e.status == Elevator.MOVING_DOWN:
                    distance_from_called = working_e.current_floor - working_e.called_floor
                else:
                    distance_from_called = 0

                # if the distance to the request is not 0 and the requested floor is from the controller
                # if the requested floor is not from the controller then it is from a user in the elevator
                # therefore we cannot reassign this elevators requests
                if distance_from_called and working_e.requested_floors[working_e.called_floor]['controller']:
                    distance_from_request = self.num_floors
                    for waiting_e in waiting_elevators:
                        # flag to make sure there are no user requested stops for the elevator
                        # if a user needs to stop somewhere then we don't want to stop before the user has a chance to get off.
                        no_user_requests = True

                        # if the waiting elevator is closer to the called floor then the working elevator then perhaps we can reassign the request
                        if waiting_e.current_floor < working_e.called_floor:
                            if working_e.called_floor - waiting_e.current_floor < distance_from_called:
                                for i in range(working_e.called_floor - waiting_e.current_floor):
                                    # make sure there are not user requests
                                    if working_e.requested_floors[i + waiting_e.current_floor]['elevator']:
                                        no_user_requests = False
                                if no_user_requests:
                                    # if no user requests the reassign the elevator to the closest elevator
                                    if distance_from_request > working_e.called_floor - waiting_e.current_floor:
                                        distance_from_request = working_e.called_floor - waiting_e.current_floor
                                        best_elevator = waiting_e
                        # this is the same checks as above but only occurs if the elevator is above the requested floor.
                        # the previous logic was if the elevator was below the requested floor.
                        else:
                            if waiting_e.current_floor - working_e.called_floor < distance_from_called:
                                for i in range(waiting_e.current_floor - working_e.called_floor):
                                    if working_e.requested_floors[waiting_e.current_floor-i]['elevator']:
                                        no_user_requests = False
                                if no_user_requests:
                                    if distance_from_request > waiting_e.current_floor - working_e.called_floor:
                                        distance_from_request = waiting_e.current_floor - working_e.called_floor
                                        best_elevator = waiting_e

                    # cancel and reassign the requested elevator
                    if best_elevator:
                        best_elevator.controller_call(working_e.called_floor, working_e.request_direction)
                        best_elevator.pending_calls = working_e.pending_calls
                        self.cancel(working_e)

    def cleanup_crash(self):
        # add current requests in crashed elevator to queue for reassignment
        # once the request is reassigned then clear out the data for the elevator and set the status to OFFLINE
        for i in self.elevators:
            if self.elevators[i].status == Elevator.CRASH:
                for floor in self.elevators[i].requested_floors:
                    # pass the current request into the queue
                    if self.elevators[i].requested_floors[floor]['controller']:
                        self.queue.put((self.elevators[i].request_direction, floor))
                    # pass the pending requests into the queue
                    for floor in self.elevators[i].pending_calls:
                        self.queue.put((self.elevators[i].request_direction, floor))
                self.elevators[i].set_offline()


    def run(self):
        while True:
            time.sleep(1)
            try:
                # pull request from the queue.
                (direction, floor) = self.queue.get_nowait()
                awaiting_service = True
                best_elevator = None
                distance_from_request = self.num_floors

                # check to see if another elevator is servicing this same request.  Just in case a user inputs that same command twice
                # we don't want to send another elevator to service the same request.
                for i in self.elevators:
                    if self.elevators[i].request_direction == direction and self.elevators[i].requested_floors[floor]['controller']:
                        awaiting_service = False

                while awaiting_service:
                    # awaiting_service is used to continue the loop until we can service a request
                    for i in self.elevators:
                        # if an elevator is waiting then send the closest elevator to the request
                        if self.elevators[i].status == Elevator.WAITING and not self.elevators[i].crash:
                            if floor > self.elevators[i].current_floor:
                                if floor - self.elevators[i].current_floor < distance_from_request:
                                    distance_from_request = floor - self.elevators[i].current_floor
                                    best_elevator = i
                            else:
                                if self.elevators[i].current_floor - floor < distance_from_request:
                                    distance_from_request = self.elevators[i].current_floor - floor
                                    best_elevator = i

                    if best_elevator >= 0:
                        # send the best elevator to the requested floor and break the loop.
                        self.call(best_elevator, floor, direction)
                        awaiting_service = False

                    if awaiting_service:
                        # if no elevator is WAITING and if there is request closer than the pending request of working elevator
                        # then switch nearest elevator's request to secondary request and make new request terminal stop
                        # make sure that we check the requested direction so that we can properly service the previous request
                        for i in self.elevators:
                            if self.elevators[i].request_direction == direction and not self.elevators[i].crash:
                                if self.elevators[i].status == Elevator.MOVING_UP and self.elevators[i].requested_floors[self.elevators[i].called_floor]['controller'] and direction == Elevator.MOVING_DOWN:
                                    if floor > self.elevators[i].called_floor:
                                        if floor - self.elevators[i].called_floor < distance_from_request:
                                            distance_from_request = floor - self.elevators[i].called_floor
                                            best_elevator = i

                                elif self.elevators[i].status == Elevator.MOVING_DOWN and self.elevators[i].requested_floors[self.elevators[i].called_floor]['controller'] and direction == Elevator.MOVING_UP:
                                    if floor < self.elevators[i].called_floor:
                                        if self.elevators[i].called_floor - floor < distance_from_request:
                                            distance_from_request = self.elevators[i].called_floor - floor
                                            best_elevator = i

                        if best_elevator >= 0:
                            # switch call finds changes the terminal request and stores the old state in a pending array.
                            # a switch can happen multiple times for an elevator.
                            self.switch_call(best_elevator, floor)

                    #if an elevator is crashed then reassigned the requests to the queue
                    self.cleanup_crash()

                    # optimize requests in relation to elevators that were working and now have a changed status to WAITING
                    self.optimize()
            except:
                #if an elevator is crashed then reassigned the requests to the queue
                self.cleanup_crash()

                # optimize requests in relation to elevators that were working and now have a changed status to WAITING
                self.optimize()


    def request_up(self, floor):
        # attempt to send an elevator to service a request but if that is not successful store the request in a queue to be processed later
        # there are num_floor-1 floors and the num_floor-1th cannot request up since it is the top floor.
        # therefore we check for < num_floor-1
        if floor < self.num_floors-1 and floor >= 0:
            self.queue.put((Elevator.MOVING_UP, floor))

    def request_down(self, floor):
        # attempt to send an elevator to service a request but if that is not successful store the request in a queue to be processed later
        if floor > 0 and floor <= self.num_floors-1:
            self.queue.put((Elevator.MOVING_DOWN, floor))

    def request_floor(self, elevator_num, floor):
        # send an elevator on a user request (person inside the elevator)
        if floor >= 0 and floor <= self.num_floors-1:
            self.elevators[elevator_num].elevator_call(floor)

    def call(self, elevator_num, floor, direction):
        # send an elevator on a request (person requesting elevator from a floor)
        self.elevators[elevator_num].controller_call(floor, direction)

    def switch_call(self, elevator_num, floor):
        # switch an elevator's request because a more optimal elevator has come available.
        self.elevators[elevator_num].controller_switch_call(floor)

    def crash(self, elevator_num):
        # switch an elevator's request because a more optimal elevator has come available.
        self.elevators[elevator_num].crash_elevator()

    def cancel(self, working_e):
        working_e.cancel_elevator()




