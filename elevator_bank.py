'''
Created on April 27, 2012
@author: Jonathan Kowalski

Main initializer for the elevator bank
'''


from control import Controller
import sys
import getopt


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    floors = 0
    elevators = 0

    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "f:e:h", ["floors=", "elevators=", "help"])
        except getopt.error, msg:
             raise Usage(msg)

        for opt, arg in opts:
            if opt in ('-e', '--elevators'):
                elevators = arg
            if opt in ('-f', '--floors'):
                floors = arg

        if elevators > 0 and floors > 0:
            c = Controller(int(elevators), int(floors))
            c.start()
            process = True

            while process:
                var = raw_input("Enter command: ")
                var =  var.split(':')
                command = var[0]
                if command == 'quit':
                    process = False
                else:
                    floor = var[1]

                    if command == 'up':
                        # command expected in the form of 'up:floor_num'
                        c.request_up(int(floor))
                    elif command == 'down':
                        # command expected in the form of 'down:floor_num'
                        c.request_down(int(floor))
                    elif command == 'elevator':
                        # command expected in the form of 'elevator:floor_num:elevator_num'
                        elevator_num = var[2]
                        c.request_floor(elevator_num, floor)

        else:
            print 'Elevator Bank Program'
            print 'usage: python elevator_bank.py -f num_floors -e num_elevators\n'
            print 'f num_floors    : enter the number of floors as a positive integer.  The first floor is 0.'
            print 'e num_elevators : enter the number of elevators as a positive integer.  The first elevator is 0.'

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())


