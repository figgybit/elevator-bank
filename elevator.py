'''
Created on April 27, 2012
@author: Jonathan Kowalski

Class for Elevator

'''

import time
import datetime
import threading
import logging
logging.basicConfig(filename='elevator.log',level=logging.DEBUG)


class Elevator(threading.Thread):

    # The possibles statuses of the elevator
    WAITING = 1
    MOVING_UP = 2
    MOVING_DOWN = 3
    SERVICING = 4
    CRASH = 5
    OFFLINE = 6

    # Amount of time it takes to move between floors
    TRANSVERSE_INTERVAL = 5
    # Amount of time it takes to stop at a floor
    STOPPING_INTERVAL = 10
    # Amount of time we wait for a user to enter the elevator and select a floor before servicing another external request
    SERVICING_INTERVAL = 10
    # Amount of time we wait for a user to enter the elevator
    ENTRY_INTERVAL = 5
    # Amount of time an elevator is offlne after it crashes
    OFFLINE_INTERVAL = 300

    def __init__(self, num_floors):
        # Elevator starts at floor 0 and are waiting for a request
        self.status = Elevator.WAITING

        # This is the direction that a user on a floor is requesting to go in.
        self.request_direction = Elevator.WAITING

        # this is the floor it is currently on
        self.current_floor = 0

        # this is the maximum or minimum floor depending on it's direction
        self.called_floor = 0

        # if another elevator that was working changes to a waiting state and it is closer to the called floor
        # then this elevator will be cancelled and the other elevator will take over it's request
        self.cancel = False

        # flag to determine if the elevator is crashed.
        self.crash = False

        # flag to keep the thread working.  using in the testing framework
        self.running = True

        # If all elevators are working and a new controller request that has the same requested_direction
        # then the elevator that is closest will change it's called_floor and hold the previous requests as a pending_request.
        self.pending_calls = []

        # the elevator takes requests from a person in the elevator.
        # the elevator takes requests from the controller for people outside of the elevator.
        # the elevator is allowed to stop on any floor between it's current_floor and it's called_floor.
        # the elevator is allowed to go farther than the called_floor if a user in the elevator requests it.
        # the elevator is allowed to go farther than the called_floor if the controller requests it.
        # The controller will not be programmed to override the called_floor although it is allowed.
        self.requested_floors = dict()
        for i in range(num_floors):
            self.requested_floors[i] = {'elevator':False, 'controller':False}
        threading.Thread.__init__(self)

    def run(self):
        logging.info('Starting Elevator '+self.getName())
        while self.running:
            # this is the loop that initiates the movement of the elevator.
            if self.called_floor != self.current_floor and not self.crash:
                ####self.requested_floors[self.called_floor]['controller'] = True
                self.traverse()
            if self.status == Elevator.OFFLINE:
                time.sleep(Elevator.OFFLINE_INTERVAL)
                self.status = Elevator.WAITING
                self.crash = False


    def traverse(self):
        logging.info('Elevator '+self.getName() + ' On Floor: ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))

        # the direction of the elevator is determined by the difference between the called_floor and the current_floor
        if self.called_floor < self.current_floor:
            self.status = Elevator.MOVING_DOWN
            interval = -1
        else:
            self.status = Elevator.MOVING_UP
            interval = 1

        # the elevator will continue to move as long as the elevator is not at the called_floor
        while self.current_floor != self.called_floor and not self.cancel and not self.crash:
            self.current_floor += interval

            # when the elevator arrives at the called_floor:
            # -it stops on this floor
            # -it resets the requests, in case a person in the elevator requests stops not in the path.
            # -it sets the status to SERVICING, so that the user has time to press a button.
            # -the elevator is not programmed to go back down to the 0th floor,
            #     since there is no guarentee that the 0th floor is the next request although it is highly probable.
            #     I have noticed that most elevators will decend to 1/3 of the way to the ground floor,
            #     but I think this is not energy efficient.  Perhaps it makes the users happy when they arrive in the building,
            #     but I am more concerned with being energy efficient.  It makes me unhappy when I want to leave the building,
            #     since I live on the top floor of my apartment building.   If I come to the top of my apartment with the desire to leave shortly after,
            #     then what is the point for the elevator to descend back to the 1/3 of the way to ground level.  What a waste of energy!
            if (self.current_floor) == self.called_floor:
                time.sleep(Elevator.STOPPING_INTERVAL)
                logging.info('Elevator '+self.getName() + ' Stopped Final Destination: ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))

                for floor in self.requested_floors:
                    self.requested_floors[floor]['elevator'] = False
                    self.requested_floors[floor]['controller'] = False
                self.status = Elevator.SERVICING

            # if the elevator arrives at a floor that is requested as a stop between the final destinate.  Then it will stop.
            # stops can be requested by users in the elevator or by users on the floors (by the controller)
            elif self.requested_floors[self.current_floor]['elevator'] or self.requested_floors[self.current_floor]['controller']:
                time.sleep(Elevator.STOPPING_INTERVAL)
                logging.info('Elevator '+self.getName() + ' Stopped On Floor: ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))

            # if there is no request the the elevator should pass that floor.
            else:
                time.sleep(Elevator.TRANSVERSE_INTERVAL)
                logging.info('Elevator '+self.getName() + ' Passed Floor: ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))

        if self.cancel:
            # if this elevator is cancelled then the logic below is used to stop the elevator and reset it to a WAITING state.
            logging.info('Elevator '+self.getName() + ' was Cancelled on Floor : ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))
            for floor in self.requested_floors:
                self.requested_floors[floor]['elevator'] = False
                self.requested_floors[floor]['controller'] = False

            self.status = Elevator.WAITING
            self.request_direction = Elevator.WAITING
            self.pending_calls = []
            self.called_floor = self.current_floor
            self.cancel = False
        elif self.crash:
            # logic to handle a crashed elevator
            logging.info('Elevator '+self.getName() + ' has Crashed near Floor : ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))
            self.status = Elevator.CRASH
        else:
            if self.pending_calls:
                # if the elevator has pending_calls then the elevator will not wait for a user to press a button
                # but the elevator will wait for the user to enter the elevator
                # once the user has entered the elevator will service the pending requests
                time.sleep(Elevator.ENTRY_INTERVAL)
                if self.request_direction == Elevator.MOVING_UP:
                    self.pending_calls.sort()
                else:
                    self.pending_calls.reverse()
                for i in range(len(self.pending_calls)):
                    self.controller_call(self.pending_calls.pop(), self.request_direction)
            else:
                # if the elevator doesn't have any pending requests then it waits for the user to enter and press a button
                logging.info('Elevator '+self.getName() + ' Servicing on Floor : ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))
                time.sleep(Elevator.SERVICING_INTERVAL)
                self.request_direction = Elevator.WAITING
                self.status = Elevator.WAITING
                logging.info('Elevator '+self.getName() + ' Waiting on Floor : ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))

    def controller_call(self, floor, direction):
        # if the call is greater than the minimum or maximum depending on the direction then it should reset the final destination.
        # if the elevator is WAITING then it should set the final desination.
        if (self.status == Elevator.MOVING_DOWN and self.called_floor > floor) or (self.status == Elevator.MOVING_UP and self.called_floor < floor) or (self.status in (Elevator.WAITING,Elevator.SERVICING)):
            self.called_floor = floor
            self.request_direction = direction
            logging.info('Elevator '+self.getName() + ' Control Request Received for Floor : ' + str(floor))
        self.requested_floors[floor]['controller'] = True

    def elevator_call(self, floor):
        # if the call is greater than the minimum or maximum depending on the direction then it should reset the final destination.
        # if the elevator is WAITING then it should set the final desination.
        if (self.status == Elevator.MOVING_DOWN and self.called_floor > floor) or (self.status == Elevator.MOVING_UP and self.called_floor < floor) or (self.status in (Elevator.WAITING,Elevator.SERVICING)):
            self.called_floor = floor
            logging.info('Elevator '+self.getName() + ' User Request Received for Floor : ' + str(floor))
            if floor > self.current_floor:
                self.status = Elevator.MOVING_UP
            else:
                self.status = Elevator.MOVING_DOWN

        self.requested_floors[floor]['elevator'] = True

    def controller_switch_call(self, floor):
        # if the elevator is close to a pending call for the same direction it is requested to go once it arrives at the requested floor
        # and no other elevators can service the request then the elevator will switch it's terminal floor
        # and store the previous terminal floor in a pending array.
        self.requested_floors[self.called_floor]['controller'] = False
        self.pending_calls.append(self.called_floor)
        self.called_floor = floor

    def crash_elevator(self):
        self.crash = True

    def cancel_elevator(self):
        self.cancel = True

    def set_offline(self):
        logging.info('Elevator '+self.getName() + ' is going OFFLINE on Floor : ' + str(self.current_floor) + ' ' + str(datetime.datetime.now()))
        for floor in self.requested_floors:
            self.requested_floors[floor]['elevator'] = False
            self.requested_floors[floor]['controller'] = False

        self.status = Elevator.OFFLINE
        self.request_direction = Elevator.WAITING
        self.pending_calls = []
        self.called_floor = self.current_floor


