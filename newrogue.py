#########################
# NEW VERSION 12/4/2015 #
#########################

import libtcodpy as libtcod
import math
import textwrap
import shelve
import random 
import time

###########
# STATICS #
###########

FOV_ALGO = 8
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 9

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 60

MAP_WIDTH = 80
MAP_HEIGHT = 50

BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2 
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2 
MSG_HEIGHT = PANEL_HEIGHT - 1 

color_dark_wall = libtcod.darkest_grey
color_dark_ground = libtcod.darker_grey

color_light_wall = libtcod.desaturated_blue
color_light_ground = libtcod.light_blue

#parameters for dungeon generator
ROOM_MAX_SIZE = 30
ROOM_MIN_SIZE = 3
MAX_ROOMS = 50


############
# CONTROLS #
############

def handle_keys():
	global fov_recompute
	global keys, mouse
	
	
	libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
	
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#alt enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	
	elif key.vk == libtcod.KEY_ESCAPE:
		return True #exit game
	
	if game_state == 'playing':
	
		if key.vk is not libtcod.KEY_SHIFT:	
	
			#movement keys (arrows + numpad)
			if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
				player.move(0, -1)
				
			elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
				player.move(0, 1)
				
			elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
				player.move(-1, 0)	
				
			elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
				player.move(1, 0)
				
			#diagonals
			elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
				player.move(-1, -1)
				
			elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
				player.move(1, -1)
				
			elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
				player.move(-1, 1)
				
			elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
				player.move(1, 1)
			
			elif key.vk == libtcod.KEY_KP5:
				pass #do nothing i.e. wait for monster to come to you

			
			
			#mouse	
			if mouse.lbutton_pressed or mouse.lbutton:
				for i in range(1):
					player.move_towards(mouse.cx, mouse.cy)
					#libtcod.console_put_char(con, player.x, player.y, '.', libtcod.green)
					time.sleep(.05)
			
			#rightclick teleports player to the cursor
			if mouse.rbutton_pressed or mouse.rbutton:
				player.x = mouse.cx
				player.y = mouse.cy
				
			
		fov_recompute = True
		
		
###########		
# CLASSES #		
###########			
			
class Tile:
	def __init__(self, blocked, block_sight = None, explored = False):
		self.blocked = blocked
		
		#all tiles start unexplored
		self.explored = False	
		
		#if tile is blocked, sight is also blocked 
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight

class Object:
	def __init__(self, x, y, char, color, name, status):
		self.x = x
		self.y = y 
		self.char = char 
		self.color = color 
		self.name = name
		self.status = status
		
		
	def move(self, dx, dy):
		if not map[self.x + dx][self.y + dy].blocked:
			self.x += dx 
			self.y += dy
			
	def	freeze(self, turns=1):
		if self == player and self.status is not "frozen":
			for t in range(turns):
				self.status == "frozen"
			self.status == "fine"
			return
	

	
	def draw(self):
		#only show when visible to player
		if libtcod.map_is_in_fov(fov_map, self.x, self.y):
			libtcod.console_set_default_foreground(con, self.color)
			libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
		
	def clear(self):
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

	def move_towards(self, target_x, target_y):
	 #do some stuff before moving at all
		dx = target_x - self.x 
		dy = target_y - self.y 
		
		if self == player:
			if dx > 0:
				dx = 1
			if dx < 0:
				dx = -1 
			if dy > 0:
				dy = 1 
			if dy < 0:
				dy = -1

		self.move(dx, dy)

class Shape:
	#rect
	def __init__(self, x, y, w, h):
	
		self.x1 = x
		self.y1 = y 
		self.x2 = x + w 
		self.y2 = y + h 
	
	def center(self):
		center_x = (self.x1 + self.x2) / 2 
		center_y = (self.y1 + self.y2) / 2 
		return (center_x, center_y)
		
	def intersect(self, other):
		#returns true if this rectangle intersects with another one
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)	
		
####################
# GLOBAL FUNCTIONS #
####################	

def display_status():
	if player.status is not None:
		message(player.status, libtcod.green)

def create_room(room):
	global map

	#centre of circle
	cx = (room.x1 + room.x2) / 2 
	cy = (room.y1 + room.y2) / 2 
	
	#radius of circle; makes it fit in the room
	width = room.x2 - room.x1
	height = room.y2 - room.y1
	r = min(width, height) / 2
	
	#smaller radius to fit in the bigger one
	width2 = room.x2 - room.x1 #- 1
	height2 = room.y2 - room.y1 #- 1
	r2 = min(width2, height2) / 3
	
	for x in range(room.x1, room.x2):
		for y in range(room.y1, room.y2):
			if math.sqrt((x - cx) ** 2 + (y - cy) ** 2) <= r:
				map[x][y].blocked = True
				map[x][y].block_sight = True

	for x in range(room.x1, room.x2):
		for y in range(room.y1, room.y2):
			if math.sqrt((x - cx) ** 2 + (y - cy) ** 2) <= r2:
				map[x][y].blocked = False
				map[x][y].block_sight = False	
				
def display_border(char, color):
	global map
	
	#define the border around the map
	for y in range(MAP_HEIGHT - 8):
		x = 0
		libtcod.console_print_ex(overlay, x, y, libtcod.BKGND_NONE, libtcod.LEFT, char )
		#block it
		map[x][y].blocked = True
		map[x][y].block_sight = True
	
	for y in range(MAP_HEIGHT - 8):
		x = MAP_WIDTH - 1
		libtcod.console_print_ex(overlay, x, y, libtcod.BKGND_NONE, libtcod.LEFT, char )
		#block it
		map[x][y].blocked = True
		map[x][y].block_sight = True
		
	for x in range(MAP_WIDTH):
		y = 0
		libtcod.console_print_ex(overlay, x, y, libtcod.BKGND_NONE, libtcod.LEFT, char )
		#block it
		map[x][y].blocked = True
		map[x][y].block_sight = True	
		
	for x in range(MAP_WIDTH):
		y = MAP_HEIGHT - 8
		libtcod.console_print_ex(overlay, x, y, libtcod.BKGND_NONE, libtcod.LEFT, char )
		#block it
		map[x][y].blocked = True
		map[x][y].block_sight = True
			
			
def make_map():
	global map
	
	#fill with unblocked tiles
	map = [[ Tile(False)
		for y in range(MAP_HEIGHT) ]
			for x in range(MAP_WIDTH) ]
	

		
	#some cornerstones for testing stuff
	#topleft
	map[0][0].blocked = True
	map[0][0].block_sight = True
	#bottomleft
	map[0][42].blocked = True
	map[0][42].block_sight = True
	#topright
	map[79][0].blocked = True
	map[79][0].block_sight = True
	#bottomright
	map[79][42].blocked = True
	map[79][42].block_sight = True

	rooms = []
	num_rooms = 0
	
	# GO!
	for r in range(MAX_ROOMS):
		#random width and height
		w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		#random position without going out of boundaries of map
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 2) #changed from 1 to see
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 2) #if it helps with the edge of the map (seems like it does)
			
		#making a shape 
		new_room = Shape(x, y, w, h)
		
		#run through other rooms and see if they intersect with this one
		failed = False
		
		for other_room in rooms:
			if new_room.intersect(other_room):
				#if width is lower than this number, go ahead anyway
				#otherwise, nope, intersects and is also too big
				if w and h > 15:			
					failed = True
					break	
				if w and h < 3:
					failed = True
					break			
					
		if not failed:
			
			create_room(new_room)
			
			#center coords of new room, will be useful later
			(new_x, new_y) = new_room.center()
			
			#optional bit of code to label rooms
			#room_no = Object(new_x, new_y, chr(65+num_rooms), 'Room Number', libtcod.white, blocks=False)
			#objects.insert(0, room_no) #draw early so monsters are drawn on top
					

			
					
					
			#finally, append the new room to the list
			rooms.append(new_room)
			num_rooms += 1
	
		if num_rooms == 0:
		#first room, where player starts
			player.x = new_x
			player.y = new_y
			
			#make sure the players room is clear
			map[new_x][new_y].blocked = False
			map[new_x][new_y].block_sight = False

	

#fetching the coordinates of the mouse, returns them as string for display
def get_coords_under_mouse():
	global mouse
	
	coords = str(mouse.cx) + ',' + str(mouse.cy)
	return coords
	
def display_cursor_tile(ctile=None):
	global mouse
	
	(px, py) = (player.x, player.y)
	(x, y) = (mouse.cx, mouse.cy)
	
	#tile changes depending on whats under the mouse
	if px == x and py == y and object == player:
		#it's you
		libtcod.console_print_ex(overlay, x, y, libtcod.BKGND_NONE, libtcod.LEFT, ' ' )
	elif object == object and mouse.lbutton:
		libtcod.console_print_ex(overlay, x, y, libtcod.BKGND_NONE, libtcod.LEFT, 'o' )
	else:	
		#display the default cursor
		libtcod.console_print_ex(overlay, mouse.cx, mouse.cy, libtcod.BKGND_SET, libtcod.LEFT, 'O' )	

def display_cursor_trail():
	global mouse
    
	(x, y) = (mouse.cx, mouse.cy)
	
	mouseCoords = [[x, y]]
	for i in range(len(mouseCoords)):
		for j in range(len(mouseCoords[i])):
			#print mouseCoords[i],[j]
			libtcod.console_print_ex(con, x, y, libtcod.BKGND_NONE, libtcod.LEFT, ' ' )
		
		
def message(new_msg, color = libtcod.white):
	#split if needed
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
	
	for line in new_msg_lines:
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]
			
		game_msgs.append((line, color))
	
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	bar_width = int(float(value) / maximum * total_width)
	
	libtcod.console_set_default_background(panel, back_color)
	libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
	
	libtcod.console_set_default_background(panel, bar_color)
	if bar_width > 0:
		libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
		
	libtcod.console_set_default_foreground(panel, libtcod.white)
	libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
		name + ': ' + str(value) + '/' + str(maximum))
		
def render_all():
	global fov_map
	global fov_recompute
	
	if fov_recompute:
		fov_recompute = False 
		libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
		
		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				visible = libtcod.map_is_in_fov(fov_map, x, y)
				wall = map[x][y].block_sight
				
				if not visible:		
					if map[x][y].explored:
						if wall:
							libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
						else:
							libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
				else:
					if wall:
						libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
					else:
						libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
					#visible, so explore it:
					map[x][y].explored = True
			
		#draw all objects in the list
		for object in objects:
			object.draw()
			
			
		#gui
		libtcod.console_set_default_background(panel, libtcod.black)
		libtcod.console_clear(panel)
		
		#print messages one at a time
		y = 1
		for (line, color) in game_msgs:
			libtcod.console_set_default_foreground(panel, color)
			libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
			y += 1

		#coords under mouse gets called here	
		libtcod.console_set_default_foreground(panel, libtcod.light_purple)
		libtcod.console_print_ex(panel, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT, get_coords_under_mouse())
		
		#mouse stuff
		libtcod.mouse_show_cursor(False)
		
		display_cursor_tile()
		#display_cursor_trail()
		display_status()
		display_border('>', libtcod.red)

		
		#BLIT CONSOLE#
		libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)

		#BLIT PANEL#
		libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)
		
		#BLIT OVERLAY#
		libtcod.console_blit(overlay, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0, 0.5, 0.1)

	
def initialize_fov():
	global fov_recompute, fov_map
	fov_recompute = True
	
	#create the FOV map, according to generated map
	fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
	
	libtcod.console_clear(con) #unexplored areas start with the default bg color (black)
	
	
#########################
# Initialization & Main #
#########################

libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'newrogue', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
#overlay for gui effects
overlay = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

mouse = libtcod.Mouse()
key = libtcod.Key()

player = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.white, name="Timmy", status="fine")

objects = [player]
game_msgs = []

make_map()
initialize_fov()

game_state = 'playing'
player_action = None

############
# GAMELOOP #
############

while not libtcod.console_is_window_closed():

	render_all()
	
	libtcod.console_clear(overlay)	
	libtcod.console_flush()

	
	for object in objects:
		object.clear()
	
	
	exit = handle_keys()
	if exit:
		break