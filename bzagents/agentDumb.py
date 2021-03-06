#!/usr/bin/python -tt

# An incredibly simple agent.  All we do is find the closest enemy tank, drive
# towards it, and shoot.  Note that if friendly fire is allowed, you will very
# often kill your own tanks with this code.

#################################################################
# NOTE TO STUDENTS
# This is a starting point for you.  You will need to greatly
# modify this code if you want to do anything useful.  But this
# should help you to know how to interact with BZRC in order to
# get the information you need.
#
# After starting the bzrflag server, this is one way to start
# this code:
# python agent0.py [hostname] [port]
#
# Often this translates to something like the following (with the
# port name being printed out by the bzrflag server):
# python agent0.py localhost 49857
#################################################################

import sys
import math
import time
import random
import math

from bzrc import BZRC, Command

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
    
        #self.last_move = time.time()
        #self.last_shoot = time.time()
        #self.move_wait = random.uniform(3,8)
        #self.shoot_wait = random.uniform(1.5,2.5)
        #self.start_angle = 1000
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.mytanks, self.othertanks, self.flags, self.shots = self.bzrc.get_lots_o_stuff()
        for t in self.mytanks:
            t.last_move = time.time()
            t.last_shoot = time.time()
            t.move_wait = random.uniform(3,8)
            t.shoot_wait = random.uniform(1.5,2.5)
            t.start_angle = -1


    def to_degrees(self, radians):
        return 180 + 180 * radians / math.pi

    def tick(self):
        """Some time has passed; decide what to do next."""
        
        num_tanks = 2
        
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        
        for i in range(num_tanks):
            tank = self.mytanks[i]  
            
            tank.move_time_diff = time.time() - tank.last_move
            tank.shoot_time_diff = time.time() - tank.last_shoot
            tank.angle = mytanks[i].angle
        
        
        
        
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []

        #move_time_diff = time.time() - self.last_move
        #shoot_time_diff = time.time() - self.last_shoot
        
        for i in range(num_tanks):
        
            tank = self.mytanks[i]
        
            command = Command(tank.index, 1, 0, False)
            
            if tank.move_time_diff >= tank.move_wait:
                print 'tick'
                
                command.angvel = 1
                
                if tank.start_angle == -1:
                    tank.start_angle = tank.angle
                    
                angle_diff = self.to_degrees(tank.angle) - self.to_degrees(tank.start_angle)
                tank.angle_diff = abs((angle_diff + 180) % 360 - 180)
                
                #print self.to_degrees(tank.angle)
                #print self.to_degrees(tank.start_angle)
                print tank.angle
                
                if tank.angle_diff >= 60:
                    tank.last_move = time.time()
                    tank.move_wait = random.uniform(3,8)
                    tank.start_angle = -1
                
            if tank.shoot_time_diff >= tank.shoot_wait:
                print 'shoot'
                
                command.shoot = True

                tank.last_shoot = time.time()
                tank.shoot_wait = random.uniform(1.5,2.5)
               
            self.commands.append(command)
           
        results = self.bzrc.do_commands(self.commands)





def main():
    # Process CLI arguments.
    try:
        execname, host, port = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)

    # Connect.
    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))

    agent = Agent(bzrc)

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            agent.tick()
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
