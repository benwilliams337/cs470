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
from numpy import *

import show_field

from bzrc import BZRC, Command

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
				randField = self.build_random_field()
				potField = self.combine_fields(potField, randField, 0.8, 0.2)
				vector = [potField[0][self.world_to_field_coord(int(tank.x))][self.world_to_field_coord(int(tank.y))],potField[1][self.world_to_field_coord(int(tank.x))][self.world_to_field_coord(int(tank.y))]]
				self.align_to_pot_vector(tank, vector)

		results = self.bzrc.do_commands(self.commands)

	def align_to_pot_vector(self, tank, vector):
		# Turn to face the angle proscribed by the vector
		vector_mag = ((vector[0] ** 2 + vector[1] ** 2) ** 0.5) / (2 ** 0.5)
		
		vector_angle = math.atan2(vector[1], vector[0])
		angle_diff = self.normalize_angle(vector_angle - tank.angle)
		
		if vector_mag == 0:
			angle_diff = 0
		
		command = Command(tank.index, vector_mag, angle_diff, False)
		
		
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
		field_x = []
		field_y = []
		for c in range(len(field1[0])):
			col_x = []
			col_y = []
			for r in range(len(field1[0][c])):
				new_dx = weight1 * field1[0][c][r] + weight2 * field2[0][c][r]
				new_dy = weight1 * field1[1][c][r] + weight2 * field2[1][c][r]
				magnitude = (new_dx ** 2 + new_dy ** 2) ** 0.5
				scale_factor = 1
				if magnitude > 1:
					scale_factor = magnitude
				col_x.append(new_dx / scale_factor)
				col_y.append(new_dy / scale_factor)
			field_x.append(col_x)
			field_y.append(col_y)
		return [field_x, field_y]
		
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
		
	def build_no_flag_pot_field(self):
		enemy_flag = self.flags[random.randint(0, len(self.flags))]
		while enemy_flag.color == self.constants['team']:
			enemy_flag = self.flags[random.randint(0, len(self.flags))]
		
		enemy_flag_field = self.build_attractive_field(self.world_to_field_coord(enemy_flag.x), self.world_to_field_coord(enemy_flag.y), 1, 1)
		obstacle_field = self.build_obstacle_field()
		return self.combine_fields(enemy_flag_field, obstacle_field, 1, 2)
		
		
	def build_have_flag_pot_field(self):
		# Build an attractive field on our base
		bases = self.bzrc.get_bases()
		my_base = 0
		for base in bases:
			if base.color == self.constants['team']:
				my_base = base
				break
				
		base_center_x = self.world_to_field_coord((my_base.corner1_x + my_base.corner3_x) / 2)
		base_center_y = self.world_to_field_coord((my_base.corner1_y + my_base.corner3_y ) / 2)
		base_radius = self.world_to_field_dist(abs(my_base.corner1_x - my_base.corner3_x) / 2)
		
		base_field =  self.build_attractive_field(base_center_x, base_center_y, base_radius, 2)
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
			center_x = self.world_to_field_coord((x_min + x_max) / 2)
			center_y = self.world_to_field_coord((y_min + y_max) / 2)
			radius = self.world_to_field_dist(max(x_max - x_min, y_max - y_min) / 2)
			obs_respulse_field = self.build_repulsive_field(center_x, center_y, radius, 5)
			obs_tangent_field = self.build_tangential_field(center_x, center_y, radius, 5)
			obs_field = self.combine_fields(obs_respulse_field, obs_tangent_field, 1, 0.5)
			obs_fields.append(obs_field);
			weights.append(1)
			
		result = self.combine_all_fields(obs_fields, weights)
		return result
				
		
	def build_attractive_field(self, center_x, center_y, r, s):
		
		#result = []
		result_x = zeros((self.get_field_size(), self.get_field_size()))
		result_y = zeros((self.get_field_size(), self.get_field_size()))
		
		for x in range(0, self.get_field_size()):
			#col = []
			for y in range(0, self.get_field_size()):
				
				d = ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
				angle = math.atan2(center_y - y , center_x - x)
				if d < r:
					continue
					#col.append(PotVector(0, 0))
				elif d >= r and d <= r + s:
					dx = (d - r)/s * math.cos(angle)
					dy = (d - r)/s * math.sin(angle)
					#col.append(PotVector(dx, dy))
					result_x[x][y] = dx
					result_y[x][y] = dy
				else:
					dx = math.cos(angle)
					dy = math.sin(angle)
					#col.append(PotVector(dx, dy))
					result_x[x][y] = dx
					result_y[x][y] = dy
			#result.append(col)
		return [result_x,result_y]
	
	
	def build_repulsive_field(self, center_x, center_y, r, s):
		
		result_x = zeros((self.get_field_size(), self.get_field_size()))
		result_y = zeros((self.get_field_size(), self.get_field_size()))
		
		sin_45 = (2 ** 0.5) / 2
		
		for x in range(0, self.get_field_size()):
			for y in range(0, self.get_field_size()):
				
				d = ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
				angle = math.atan2(center_y - y , center_x - x)
				if d < r:
					dx = sin_45 if math.cos(angle) < 0 else -(sin_45)
					dy = sin_45 if math.sin(angle) < 0 else -(sin_45)
					result_x[x][y] = dx
					result_y[x][y] = dy
				elif d >= r and d < r + s:
					dx = -(s + r - d)/s * math.cos(angle)
					dy = -(s + r - d)/s * math.sin(angle)
					result_x[x][y] = dx
					result_y[x][y] = dy
				else:
					continue
		return [result_x,result_y]
	
	def build_tangential_field(self, center_x, center_y, r, s):
		result_x = zeros((self.get_field_size(), self.get_field_size()))
		result_y = zeros((self.get_field_size(), self.get_field_size()))
		
		for x in range(0, self.get_field_size()):
			for y in range(0, self.get_field_size()):
				
				d = ((center_x - x) ** 2 + (center_y - y) ** 2) ** 0.5
				angle = math.atan2(center_y - y , center_x - x) + (math.pi / 2)
				if d >= r and d < r + s:
					dx = -(s + r - d)/s * math.cos(angle)
					dy = -(s + r - d)/s * math.sin(angle)
					result_x[x][y] = dx
					result_y[x][y] = dy
				else:
					continue
		return [result_x,result_y]
	
	def build_random_field(self):
		result_x = zeros((self.get_field_size(), self.get_field_size()))
		result_y = zeros((self.get_field_size(), self.get_field_size()))
		
		for x in range(0, self.get_field_size()):
			for y in range(0, self.get_field_size()):
				result_x[x][y] = random.random()
				result_y[x][y] = random.random()
		return [result_x,result_y]
	
	def get_world_size(self):
		return int(self.constants['worldsize'])
	
	def get_field_size(self):
		return self.get_world_size() / 10

	def world_to_field_coord(self, val):
		return (val + (self.get_world_size() / 2)) / 10
		
	def world_to_field_dist(self, val):
		return val / 10

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
