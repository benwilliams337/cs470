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

import show_field

from bzrc import BZRC, Command

field_to_render = []

class Agent(object):
	"""Class handles all command and control logic for a teams tanks."""

	def __init__(self, bzrc):
		self.bzrc = bzrc
		self.constants = self.bzrc.get_constants()
		self.commands = []
		self.shown_graph = False
		self.no_flag_pot_field = []
		self.have_flag_pot_field = []

	def tick(self, time_diff):
		print 'tick'
		"""Some time has passed; decide what to do next."""
		mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
		self.mytanks = mytanks
		self.othertanks = othertanks
		self.flags = flags
		self.shots = shots
		self.enemies = [tank for tank in othertanks if tank.color !=
						self.constants['team']]

		self.commands = []		

		self.build_pot_field()
		
		for tank in mytanks:
			if tank.status == "alive":
				potField = 0
				if tank.flag != "-":
					potField = self.have_flag_pot_field
				else:
					potField = self.no_flag_pot_field
				vector = potField[self.get_world_size() / 2 + int(tank.x)][self.get_world_size() / 2 + int(tank.y)]
				self.align_to_pot_vector(tank, vector)

		results = self.bzrc.do_commands(self.commands)

	def align_to_pot_vector(self, tank, vector):
		# Turn to face the angle proscribed by the vector
		vector_mag = ((vector.x ** 2 + vector.y ** 2) ** 0.5) / (2 ** 0.5)
		
		vector_angle = math.atan2(vector.y, vector.x)
		angle_diff = self.normalize_angle(vector_angle - tank.angle)
		
		if vector_mag == 0:
			angle_diff = 0
		
		command = Command(tank.index, vector_mag, angle_diff, True)
		
		
		# Append the command
		self.commands.append(command)
	
	def normalize_angle(self, angle):
		"""Make any angle be between +1/-1."""
		angle -= 2 * math.pi * int (angle / (2 * math.pi))
		if angle <= -math.pi:
			angle += 2 * math.pi
		elif angle > math.pi:
			angle -= 2 * math.pi
		return angle / math.pi
		
	def combine_fields(self, field1, field2, weight1, weight2):
		field = []
		for c in range(len(field1)):
			col = []			
			for r in range(len(field1[c])):
				col.append(field1[c][r] * weight1 + field2[c][r] * weight2)
			field.append(col)
		return field
		
	def combine_all_fields(self, fields, weights):
		scaled_weights = self.normalize_weights(weights)
		result = self.scale_field(fields[0], scaled_weights[0])
		for w, field in enumerate(fields[1:]):
			result = self.combine_fields(result, field, 1, scaled_weights[w])
		return result
	
	def scale_field(self, field, scale):
		result = []
		for c in range(len(field)):
			col = []			
			for r in range(len(field[c])):
				col.append(field[c][r] * scale)
			result.append(col)
		return result
	
	def normalize_weights(self, weights):
		s_weights = sorted(weights)
		max_weight = weights[-1]
		result = []
		for weight in weights:
			result.append(weight / max_weight)
		return result
	
	def build_pot_field(self):
		if(len(self.no_flag_pot_field) == 0):
			self.no_flag_pot_field = self.build_no_flag_pot_field()
			self.have_flag_pot_field = self.build_have_flag_pot_field()
			
		field = self.no_flag_pot_field
		
		#If there are any dynamic potential fields, add them in here
		
		if(not self.shown_graph):
			global field_to_render
			field_to_render = field
			show_field.plot_single(render_field, [], 'test.png')
			self.shown_graph = True
		
		return field
		
	def build_no_flag_pot_field(self):
		enemy_flag = self.flags[random.randrange(0, len(self.flags))]
		while enemy_flag.color == self.constants['team']:
			enemy_flag = self.flags[random.randrange(0, len(self.flags))]
		
		enemy_flag_field = self.build_attractive_field(enemy_flag.x + 400, enemy_flag.y + 400, 1, 5)
		obstacle_field = self.build_obstacle_field()
		return self.combine_fields(enemy_flag_field, obstacle_field, 1, 2)
		
		#field = [[PotVector(0,0) for j in range(self.get_world_size())] for i in range(self.get_world_size())]
		#rep_field = self.build_repulsive_field(blue_flag.x + 400, blue_flag.y + 400, 50, 50)
		#field = self.combine_fields(rep_field, attr_field)		
		
		
	def build_have_flag_pot_field(self):
		# Build an attractive field on our base
		bases = self.bzrc.get_bases()
		my_base = 0
		for base in bases:
			if base.color == self.constants['team']:
				my_base = base
				break
				
		base_center_x = ((my_base.corner1_x + my_base.corner3_x) / 2) + 400
		base_center_y = ((my_base.corner1_y + my_base.corner3_y ) / 2) + 400
		base_radius = abs(my_base.corner1_x - my_base.corner3_x) / 2
		
		base_field =  self.build_attractive_field(base_center_x, base_center_y, base_radius, 10)
		obstacle_field = self.build_obstacle_field()
		return self.combine_fields(base_field, obstacle_field, 1, 2)
		
	def build_obstacle_field(self):
		obstacles = self.bzrc.get_obstacles()
		
		obs_fields = []
		weights = []
		
		for obs in obstacles:
			sorted_x = sorted(obs, key=lambda point: point[0])
			sorted_y = sorted(obs, key=lambda point: point[1])
			x_min = sorted_x[0][0]
			x_max = sorted_x[-1][0]
			y_min = sorted_y[0][1]
			y_max = sorted_y[-1][1]
			center_x = (x_min + x_max) / 2 + 400
			center_y = (y_min + y_max) / 2 + 400
			radius = max(x_max - x_min, y_max - y_min) / 2
			obs_field = self.build_repulsive_field(center_x, center_y, radius, 50)
			obs_fields.append(obs_field);
			weights.append(1)
			
		result = self.combine_all_fields(obs_fields, weights)
		
		return result
				
		
	def build_attractive_field(self, center_x, center_y, r, s):
		result = []
		for x in range(0, self.get_world_size()):
			col = []
			for y in range(0, self.get_world_size()):
				d = ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
				angle = math.atan2(center_y - y , center_x - x)
				if d < r:
					col.append(PotVector(0, 0))
				elif d >= r and d <= r + s:
					dx = (d - r)/s * math.cos(angle)
					dy = (d - r)/s * math.sin(angle)
					col.append(PotVector(dx, dy))
				else:
					dx = math.cos(angle)
					dy = math.sin(angle)
					col.append(PotVector(dx, dy))
			result.append(col)
		return result
	
	
	def build_repulsive_field(self, center_x, center_y, r, s):
		
		result = []
		for x in range(0, self.get_world_size()):
			col = []
			for y in range(0, self.get_world_size()):
				d = ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
				angle = math.atan2(center_y - y , center_x - x)
				if d < r:
					dx = 1.0 if math.cos(angle) < 0 else -1.0
					dy = 1.0 if math.sin(angle) < 0 else -1.0
					col.append(PotVector(dx, dy))
				elif d >= r and d < r + s:
					dx = -(s + r - d)/s * math.cos(angle)
					dy = -(s + r - d)/s * math.sin(angle)
					col.append(PotVector(dx, dy))
				else:
					col.append(PotVector(0, 0))
			result.append(col)
		return result
	
	def get_world_size(self):
		return int(self.constants['worldsize'])
		
class PotVector(object):
	"""Vectors in a potential field. Values range from -1 to 1. Top-left is -1, -1, bottom-right is 1,1"""
	
	def __init__(self, x, y):
		self.x = x
		self.y = y
	
	"""OPERATOR OVERLOADING OF THE OPERATOR FOR THE POTVECTOR CLASS"""
	def __add__(self, other):
		return PotVector(self.x + other.x,self.y + other.y)

	def __mul__(self, other):
		return PotVector(other * self.x, other * self.y)
		
	def __rmul__(self, other):
		return PotVector(other * self.x, other * self.y)


def render_field(x, y, res):
	x = 399 if x == 400 else x
	y = 399 if y == 400 else y
	vector = field_to_render[x + 400][y + 400]
	return vector.x * res, vector.y * res

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
			time_diff = time.time() - prev_time
			agent.tick(time_diff)
	except KeyboardInterrupt:
		print "Exiting due to keyboard interrupt."
		bzrc.close()


if __name__ == '__main__':
	main()

# vim: et sw=4 sts=4
