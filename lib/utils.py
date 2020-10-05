from pymem import Pymem

import configparser
import math

import numpy
import mss
import cv2

import os
import time
import random

import ahk

from enum import Enum
from typing import List

config = configparser.ConfigParser()
config.read('./config.ini')

ahk = ahk.AHK()

server_name = config.get("Server", "server_name")
game_process = Pymem(config.get(server_name, "process_name"))

win_top_offset = int(config.get(server_name, "win_top_offset"))
win_left_offset = int(config.get(server_name, "win_left_offset"))
win_width = int(config.get(server_name, "win_width"))
win_height = int(config.get(server_name, "win_height"))

x_player_position_addr = int(config.get(server_name, "player_x_position"), 16)
y_player_position_addr = int(config.get(server_name, "player_y_position"), 16)

player_max_hp_addr = int(config.get(server_name, "player_max_hp"), 16)
player_cur_hp_addr = int(config.get(server_name, "player_cur_hp"), 16)

player_max_sp_addr = int(config.get(server_name, "player_max_sp"), 16)
player_cur_sp_addr = int(config.get(server_name, "player_cur_sp"), 16)

win_name = config.get(server_name, "window_name")

clip_space = {"top": win_top_offset, "left": win_left_offset,
	"width": win_width, "height": win_height}

screen = mss.mss()
random.seed()

def random_sleep(t):
	time.sleep(t + random.uniform(0, 0.015))

class error_timer:
	def __init__(self):
		self.drop_error = 0
		self.enemy_error = 0

	def drop(self, player, map, t):
		self.drop_error += t
		if self.drop_error > 15 :
			player.use_potion("Wing")
			map.target_index = map.nearest_point(player.game_position)
			self.refresh()
		else :
			self.enemy_refresh()

	def enemy(self, player, map, t):
		self.enemy_error += t
		if self.enemy_error > 15 :
			player.use_potion("Wing")
			map.target_index = map.nearest_point(player.game_position)
			self.refresh()
		else :
			self.drop_refresh()

	def drop_refresh(self):
		self.drop_error = 0

	def enemy_refresh(self):
		self.enemy_error = 0

	def refresh(self):
		self.drop_refresh()
		self.enemy_refresh()

class bot_time:
	def __init__(self):
		self.frame_time = 0
		self.last_time = 0

	def update(self):
		self.frame_time = time.time() - self.last_time
		self.last_time = time.time()

	def sleep(self, value):
		random_sleep(0.2)

class vec2:
	def __init__(self, x = 0, y = 0):
		self.x = x
		self.y = y

def diff(left_vec, right_vec):
	return vec2(left_vec.x - right_vec.x, left_vec.y - right_vec.y)

def distance(vec1, vec2):
	return math.sqrt(pow(vec1.x - vec2.x, 2) + pow(vec1.y - vec2.y, 2))

def get_player_game_position():
	return vec2(game_process.read_int(x_player_position_addr),
		game_process.read_int(y_player_position_addr))

class spell_type(Enum):
	buffing = 1
	attack = 2
	self = 3

class spell:
	def __init__(self, key, delay, cast_time, spell_type):
		self.predicates = []

		self.delay = delay
		self.cast_time = cast_time

		self.last_use_time = 0
		self.key = key
		self.type = spell_type

	def try_use(self, player, target):
		time_spend = time.time() - self.last_use_time
		if time_spend >= self.delay :
			if len(self.predicates) > 0 :
				for predicate in self.predicates :
					dist = distance(player.screen_position, target) / 30
					if predicate(dist) :
						if self.use(player, target) :
							return True
			else :
				if self.use(player, target) :
					return True
		return False

	def use(self, player, target):
		random_sleep(0.025)
		if self.type == spell_type.attack or self.type == spell_type.buffing :
			ahk.key_press(self.key)
			random_sleep(0.03)
			move_mouse_with_ofset_to(target, 3)
			random_sleep(0.05)
			ahk.click()
		elif self.type == spell_type.self :
			ahk.key_press(self.key)
			random_sleep(0.03)

		expected_hp = player.cur_hp
		if self.cast_time > 0 :
			step = self.cast_time / 5
			for i in range(0, 5):
				if player.cur_hp < expected_hp :
					return False
				else :
					time.sleep(step)
		self.last_use_time = time.time()
		return True

class cast_type(Enum):
	battle = 1
	every_time = 2

class potion:
	def __init__(self, key, delay):
		self.predicates = []

		self.delay = delay

		self.last_use_time = 0
		self.key = key

	def try_use(self):
		time_spend = time.time() - self.last_use_time
		if time_spend >= self.delay :
			if len(self.predicates) > 0 :
				for predicate in self.predicates :
					if predicate() :
						if self.use() :
							return True
			else :
				if self.use() :
					return True
		return False

	def use(self):
		ahk.key_press(self.key)
		random_sleep(0.015)

		self.last_use_time = time.time()

class player:
	def __init__(self):
		self.screen_position = vec2(win_width / 2 + 5 + win_left_offset,
			win_height / 2 + 25 + win_top_offset)

		self.game_position = get_player_game_position()

		self.max_hp = game_process.read_int(player_max_hp_addr)
		self.cur_hp = game_process.read_int(player_cur_hp_addr)
		self.last_hp = self.cur_hp

		self.max_sp = game_process.read_int(player_max_sp_addr)
		self.cur_sp = game_process.read_int(player_cur_sp_addr)

		self.spell_book = {}
		self.potions = {}

		self.auto_use_battle = []
		self.auto_use_every_time = []

		self.auto_use_potion = []

		self.auto_attack = True

	def add_potion(self, name, potion):
		self.potions[name] = potion

	def add_spell(self, name, spell):
		self.spell_book[name] = spell

	def update(self, map, time):
		self.game_position = get_player_game_position()

		self.max_hp = game_process.read_int(player_max_hp_addr)
		self.cur_hp = game_process.read_int(player_cur_hp_addr)

		self.max_sp = game_process.read_int(player_max_sp_addr)
		self.cur_sp = game_process.read_int(player_cur_sp_addr)

		if ((self.last_hp - self.cur_hp) / self.max_hp) > 0.25:
			player.use_potion("Wing")
			map.target_index = map.nearest_point(player.game_position)

		self.last_hp = self.cur_sp

		for spell_name in self.auto_use_every_time :
			self.spell_book[spell_name].try_use(self, self.screen_position)

		for potion_name in self.auto_use_potion :
			self.potions[potion_name].try_use()

	def attack(self, map, time, error_timer, target, wait_time) :
		if not self.try_spells(target):
			if self.auto_attack :
				click_to_enemy(self, target, wait_time, 2)
		map.idle_time = 0
		error_timer.enemy(self, map, time.frame_time)

	def take(self, map, time, error_timer, target, wait_time) :
		click_to_object(self, target, wait_time, 2)
		map.idle_time = 0
		error_timer.drop(self, map, time.frame_time)

	def try_spells(self, target) :
		hit = False
		for spell_name in self.auto_use_battle:
			hit = self.spell_book[spell_name].try_use(self, target)
			if hit == True :
				break
		return hit

	def use_potion(self, potion_name) :
		self.potions[potion_name].use()

	def autospell(self, spell_name, cast_t, predicates = []):
		if len(predicates) > 0 :
			for predicate in predicates :
				self.spell_book[spell_name].predicates.append(predicate)
		if cast_t == cast_type.battle :
			self.auto_use_battle.append(spell_name)
		elif cast_t == cast_type.every_time :
			self.auto_use_every_time.append(spell_name)

	def autopotion(self, potion_name, predicates):
		for predicate in predicates :
			self.potions[potion_name].predicates.append(predicate)
		self.auto_use_potion.append(potion_name)

	def enable_autoattack(self, val):
		self.auto_attack = val

	def hp_rate(self):
		return self.cur_hp / self.max_hp

	def sp_rate(self):
		return self.cur_sp / self.max_sp

def get_sprites(path, sprite_folders):
	sprites = []
	for folder in sprite_folders:
		for sprite_name in os.listdir(path + folder):
			sprites.append(cv2.imread(path + folder + '/' + sprite_name, cv2.IMREAD_GRAYSCALE))
	return sprites

def get_screen():
	return cv2.cvtColor(numpy.array(screen.grab(clip_space)), cv2.COLOR_BGR2GRAY)

def find_sprites(image, sprite_list, condition_value):
	result_list = []
	for sprite in sprite_list:
		res = cv2.matchTemplate(image, sprite, cv2.TM_CCOEFF_NORMED)
		filtred_locations = numpy.where(res >= condition_value)

		i = 0
		while i < len(filtred_locations[0]):
			x = filtred_locations[1][i]
			y = filtred_locations[0][i]
			result_list.append(vec2(x, y))
			i += 1

	return result_list

def debug_draw(image, point_list):
	for point in point_list:
		cv2.rectangle(image, (point.x, point.y), (point.x + 40, point.y + 40),
			(255, 255, 255), 3)

	cv2.imshow("babushka_debug_draw", image)

def find_nearer(player, objects):
	dist = distance(player.screen_position, objects[0])
	nearest_obj = objects[0]
	for obj in objects:
		curr_dist = distance(player.screen_position, obj)
		if curr_dist < dist:
			dist = curr_dist
			nearest_obj = obj
	return nearest_obj

def move_mouse_to(pos, speed2):
	ahk.mouse_move(pos.x, pos.y, speed=speed2 + random.uniform(0, 1), blocking=True)

def move_mouse_with_ofset_to(pos, speed2):
	ahk.mouse_move(pos.x + 20 + win_left_offset, pos.y + 20 + win_top_offset,
		speed=speed2, blocking=True)

def click_to_object(player, obj, t, speed2):
	random_sleep(0.05)
	ahk.mouse_move(obj.x + 10 + win_left_offset, obj.y + 5 + win_top_offset,
		speed=speed2, blocking=True)
	random_sleep(0.08)
	ahk.click()
	move_mouse_to(player.screen_position, 2)
	random_sleep(t)

def click_to_enemy(player, obj, t, speed2):
	ahk.mouse_move(obj.x + 20 + win_left_offset, obj.y + 20 + win_top_offset,
		speed=speed2, blocking=True)
	random_sleep(0.08)
	ahk.key_down('Control')
	ahk.click()
	move_mouse_to(player.screen_position, 2)
	ahk.key_up('Control')
	random_sleep(t)

class node	:
	def __init__(self, x, y):
		self.pos = vec2(x, y)
		self.chain = []
		self.time = time.time()

	def add_chain(self, index):
		self.chain.append(index)

class map:
	def __init__(self):
		self.nodes: List[node] = []

		self.current_index = 9999
		self.target_index = 9999

		self.idle_time = 0
		self.last_position = vec2(9999, 9999)

	def save_map(self, path, filename):
		file = open(path + filename, 'w')

		for i in range(len(self.nodes)) :
			file.write(str(self.nodes[i].pos.x) + ' ' + str(self.nodes[i].pos.y)
			 	+ ' ' + str(self.nodes[i].chain) + '\n')

		file.close()

	def load_map(self, path, filename):
		self.__init__()
		file = open(path + filename, 'r')

		for line in file :
			line = line.replace(',', '')
			line = line.replace('[', '')
			line = line.replace(']', '')
			line = line.replace('\n', '')
			split_line = line.split(' ')

			nd = node(int(split_line[0]), int(split_line[1]))
			for value in range(2, len(split_line)):
				nd.add_chain(int(split_line[value]))

			self.nodes.append(nd)

		file.close()

	def add_node(self, x, y):
		nd = node(x, y)
		self.nodes.append(nd)

	def add_chain(self, left, right):
		self.nodes[left].add_chain(right)
		self.nodes[right].add_chain(left)

	def nearest_point(self, position):
		point_index = 0
		dist = distance(position, self.nodes[0].pos)

		i = 1
		while i < len(self.nodes):
			checked_dist = distance(position, self.nodes[i].pos)
			if(checked_dist < dist):
				point_index = i
				dist = checked_dist
			i += 1
		return point_index

	def in_range(self, index, position, range):
		return distance(position, self.nodes[index].pos) < range

	def vec_dir(self, index, position):
		vec = diff(self.nodes[index].pos, position)
		dist = distance(position, self.nodes[index].pos)
		if dist != 0 :
			return vec2(vec.x / dist, vec.y / dist)
		return vec2(0, 0)

	def choose_older_node(self, index):
		next_index = self.nodes[index].chain[0]
		time = self.nodes[next_index].time

		i = 1
		while i < len(self.nodes[index].chain):
			chained_node = self.nodes[index].chain[i]
			if( self.nodes[chained_node].time < time):
				next_index = chained_node
				time = self.nodes[chained_node].time
			i += 1
		return next_index

	def check_and_fix_idle(self, player, t):
		if self.last_position.x == 9999 :
			self.last_position == player.game_position

		if distance(player.game_position, self.last_position) < 3:
			self.idle_time += t
			if self.idle_time > 5:
				player.use_potion("Wing")
				random_sleep(0.5)
				self.target_index = self.nearest_point(player.game_position)
			elif self.idle_time > 2.3:
				self.target_index = self.nearest_point(player.game_position)
		else :
			self.idle_time = 0

		self.last_position = player.game_position

	def move(self, player, t, sleep_time):
		position = player.game_position
		if self.target_index == 9999 :
			self.target_index = self.nearest_point(position)

		if self.in_range(self.target_index, position, 6):
			self.nodes[self.target_index].time = time.time()
			new_target_index = self.choose_older_node(self.target_index)
			self.current_index = self.target_index
			self.target_index = new_target_index

		vec_dir = self.vec_dir(self.target_index, position)

		ahk.mouse_move(player.screen_position.x + (140 * vec_dir.x),
			player.screen_position.y + (-140 * vec_dir.y), speed=3, blocking=True)

		self.check_and_fix_idle(player, t)

#		print(str(self.target_index) + " dir " + str(vec_dir.x) + " " + str(vec_dir.y))
#		print("from " + str(self.nodes[self.target_index].pos.x) + " " + str(self.nodes[self.target_index].pos.y))
#		print("to " + str(player.game_position.x) + " " + str(player.game_position.y))
#		print(" ")

		random_sleep(0.15)
		ahk.click()
		random_sleep(sleep_time)

def load_map(path, filename):
	m = map()
	m.load_map(path, filename)
	return m
