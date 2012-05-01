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


