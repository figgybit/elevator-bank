'''
Created on April 30, 2012
@author: Jonathan Kowalski

test objects for elevator bank
'''

from control import Controller
from elevator import Elevator
import time
import random

def case1():

    # CASE 1 - service random requests.
    elevators_num = 1
    floors_num = 40

    c = Controller(elevators_num, floors_num)
    c.start()

    # create some random floors to use for testing
    random_floors = []
    for i in range(19):
        floor = random.randrange(1,floors_num-20)
        random_floors.append(floor)

    called_floors = []

    floor = random_floors.pop()
    print floor
    called_floors.append(floor)
    c.request_up(floor)

    time.sleep(5)

    while random_floors:
        for e in c.elevators:
            if c.elevators[e].status == Elevator.WAITING:
                print 'Elevator ' + str(e)
                floor = random_floors.pop()
                print floor
                called_floors.append(floor)
                c.request_floor(e, floor)

                floor = random_floors.pop()
                print floor
                called_floors.append(floor)
                c.request_floor(e, floor)

                floor = random_floors.pop()
                print floor
                called_floors.append(floor)
                c.request_floor(e, floor)

                time.sleep(5)

    for e in c.elevators:
        c.elevators[e].running = False


def case2():

    # CASE 2 - crash elevator.
    elevators_num = 2
    floors_num = 40

    c = Controller(elevators_num, floors_num)
    c.start()

    # create some random floors to use for testing
    random_floors = []
    for i in range(10):
        floor = random.randrange(1,floors_num-1)
        random_floors.append(floor)

    called_floors = []

    floor = random_floors.pop()
    print floor
    called_floors.append(floor)
    c.request_up(floor)

    time.sleep(5)

    for e in c.elevators:
        if c.elevators[e].status != Elevator.WAITING:
            c.crash(e)

    time.sleep(10)

    running1 = True
    running2 = True
    while running1 or running2:
        if c.elevators[0].status == Elevator.WAITING or c.elevators[0].status == Elevator.OFFLINE:
            running1 = False
        if c.elevators[1].status == Elevator.WAITING or c.elevators[0].status == Elevator.OFFLINE:
            running2 = False

    for e in c.elevators:
        c.elevators[e].running = False



def case3():
    ## this case tests the optimizing function.
    ## elevator 0 will reach it's destination after elevator 2 starts to attempt to service the request.
    ## since elevator 0's status changes to WAITING and it is closer to floor 12
    ## elevator 2 is cancelled and elevator 0 will overtake the request.

    elevators_num = 3
    floors_num = 40

    c = Controller(elevators_num, floors_num)
    c.start()

    c.request_up(10)
    time.sleep(25)
    c.request_down(8)
    time.sleep(5)
    c.request_up(12)
    time.sleep(5)

    running1 = True
    running2 = True
    running3 = True

    while running1 or running2 or running3:
        if c.elevators[0].status == Elevator.WAITING:
            running1 = False
        if c.elevators[1].status == Elevator.WAITING:
            running2 = False
        if c.elevators[2].status == Elevator.WAITING:
            running3 = False

    for e in c.elevators:
        c.elevators[e].running = False



def case4():
    ## test the ability for an elevator to switch it final request and store the previous request into a pending request array
    ## initially elevator 2 will be heading for floor 12
    ## but we recieve a 5th request before any other elevators can service this request.
    ## since elevator 2 is going to floor 12.  It switches to floor 14 and then comes back down to floor 12

    elevators_num = 4
    floors_num = 40

    c = Controller(elevators_num, floors_num)
    c.start()

    c.request_up(10)
    time.sleep(1)
    c.request_down(8)
    time.sleep(1)
    c.request_down(12)
    time.sleep(1)
    c.request_up(15)
    time.sleep(1)
    c.request_down(14)
    time.sleep(1)

    running1 = True
    running2 = True
    running3 = True
    running4 = True

    while running1 or running2 or running3 or running4:
        if c.elevators[0].status == Elevator.WAITING:
            running1 = False
        if c.elevators[1].status == Elevator.WAITING:
            running2 = False
        if c.elevators[2].status == Elevator.WAITING:
            running3 = False
        if c.elevators[3].status == Elevator.WAITING:
            running3 = False

    for e in c.elevators:
        c.elevators[e].running = False








