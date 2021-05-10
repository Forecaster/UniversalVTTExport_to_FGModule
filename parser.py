#!/usr/bin/env

# Provide a desired module name as the first argument
# Provide any number of Universal VTT json files as individual arguments after that
# Each provided file will be included in the module as a map

from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile
import argparse
import base64
import json
import math
import os
import re

import fg_module

name = "DungeonFog FG Module Generator"
version = "v1.1"

parser = argparse.ArgumentParser(description="Converts one or more df2vtt files into a Fantasy Grounds module.")
parser.add_argument('module_name', metavar='M', nargs=1, help="The module name as shown within Fantasy Grounds. Also used as the filename.")
parser.add_argument('files', metavar='F', nargs='+', help="One or more paths to df2vtt files to parse into a module.")
parser.add_argument('-a', dest='author', default='DungeonFog', help="Set a custom module author. (Default: DungeonFog)")
parser.add_argument('-d', dest='door_width', default=10, type=int, nargs=1, help="Specify door width. (Default: 10)")
parser.add_argument('-v', dest='verbose', action='store_true', help="Whether detailed debugging output should be provided.")
parser.add_argument('-e', dest='extension', default='mod', help="The desired file name extension for the output module file (eg. zip). (Default: mod)")
parser.add_argument('-g', dest='grid_color', default='00000000', help="The grid color. (Default: 00000000)")
parser.add_argument('--version', action='version', version=name + ' ' + version)
parser.add_argument('-p', dest='refine_portals', action='store_true', help="Whether to refine portals (doors) and define types. Requires the Pillow module to be installed.")

args = parser.parse_args()

try:
	from PIL import Image, ImageFont, ImageDraw, ImageEnhance
except ImportError:
	if args.refine_portals:
		print("Unable to load Pillow module. This is required to use refine portals. Either run without -p or install the required module.")
		exit()

enable_zero_occluder = False

global_grid_size = 50
def pos_x(pos):
	global global_grid_size
	return pos * global_grid_size

def pos_y(pos):
	global global_grid_size
	return -(pos * global_grid_size)

def spos_x(pos):
	return str(pos_x(pos))

def spos_y(pos):
	return str(pos_y(pos))

# From: https://stackoverflow.com/a/1937202
# Answer by Andreas Brinck
def expand_line(x0, y0, x1, y1, t):
	"""
	Returns an array of four coordinate sets expanding the input line into a rectangle with thickness t
	:param x0:
	:param y0:
	:param x1:
	:param y1:
	:param t:
	:return:
	"""
	dx = x1 - x0 # delta x
	dy = y1 - y0 # delta y
	line_length = math.sqrt(dx * dx + dy * dy)
	dx /= line_length
	dy /= line_length
	# Ok, (dx, dy) is now a unit vector pointing in the direction of the line
	# A perpendicular vector is given by (-dy, dx)
	px = 0.5 * t * (-dy) # perpendicular vector with length thickness * 0.5
	py = 0.5 * t * dx

	x2 = x0 + px
	y2 = y0 + py
	x3 = x1 + px
	y3 = y1 + py
	x4 = x1 - px
	y4 = y1 - py
	x5 = x0 - px
	y5 = y0 - py
	return [{"x": x2, "y": y2}, {"x": x3, "y": y3},{"x": x4, "y": y4},{"x": x5, "y": y5}]


to_zip = []
used_image_names = []
module_name = args.module_name[0]
module_id = module_name.replace(" ", "_").lower()

xml_version = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
xml_data_version = { "version": "4.1", "dataversion": "20210302", "release": "8.1|CoreRPG:4.1" }
xml_client_root = Element("root", xml_data_version)
images = SubElement(xml_client_root, "image")

counter = 0
for file in args.files:
	json_str = None
	data = None
	if args.verbose:
		print("Processing file: " + file)
	with open(file) as f:
		json_str = f.read()
	data = json.loads(json_str)
	pixels_per_grid = data["resolution"]["pixels_per_grid"]
	global_grid_size = pixels_per_grid

	imgstring = data['image']

	imgdata = base64.b64decode(imgstring)
	exp = re.compile("(.*)(\..{2,6})")
	match = exp.match(file)
	if args.verbose:
		print(match.group(1))
		print(match.group(2))
	filename = match.group(1)
	ext = match.group(2)
	filename_counter = 0
	while used_image_names.__contains__(filename + ext):
		filename_counter += 1
		filename += "_" + str(filename_counter)
	used_image_names.append(filename + ext)
	try:
		os.mkdir("images")
	except FileExistsError:
		pass
	with open("images/" + filename + ".png", 'wb') as f:
		f.write(imgdata)
	to_zip.append("images/" + filename + ".png")

	occluders = []
	for los in data["line_of_sight"]:
		occluders.append({ "points": spos_x(los[0]["x"]) + "," + spos_y(los[0]["y"]) + "," + spos_x(los[1]["x"]) + "," + spos_y(los[1]["y"]), "type": "wall" })
	if enable_zero_occluder:
		occluders.append({ "points": "0,0,10,10", "type": "wall" })

	if args.refine_portals:
		source_img = Image.open("images/" + filename + ".png").convert("RGBA")
		draw = ImageDraw.Draw(source_img)
		portal_counter = 0
		font = ImageFont.truetype("arial.ttf", 14)
		for portal in data["portals"]:
			portal_counter += 1
			draw.text((portal["bounds"][0]["x"] * global_grid_size, portal["bounds"][0]["y"] * global_grid_size), str(portal_counter), font=font, stroke_width=4, stroke_fill=(0,0,0))
		source_img.save(filename + "_portals.png", "PNG")

		choices = [
			{ "val": 1, "name": "door", 						"expand": True, "desc": "Door: Opaque & impassable when closed, Transparent & passable when open."},
			{ "val": 2, "name": "window",						"expand": True, "desc": "Window: Always transparent. Impassable when closed, passable when open."},
			{ "val": 3, "name": "passage",		 			"expand": True, "desc": "Passage: Will leave gap in wall."},
			{ "val": 4, "name": "toggleable_wall", 	"expand": True, "desc": "Toggleable Wall: Like a door, but flush with the wall."},
			{ "val": 5, "name": "illusory_wall",		"expand": True, "desc": "Illusory Wall: - Always passable. Always opaque."},
		]

		print("A total of " + str(portal_counter) + " portals were found, these have been numbered in the file " + filename + "_portals.png in the working directory. Open this file and specify the desired type for each portal choosing from the following:")
		for c in choices:
			print(str(c["val"]) + " - " + c["desc"])
		print()
		print("list - If you wish to see this list again type 'list' instead of the type number.")
		print("1+ - You can enter a choice followed by + (ex: 2+) to set all remaining portals to that type.")
		print("r - If you enter the wrong type you can type 'r' to go back one step. You can keep doing this to go back to the beginning if you want.")
		print()

		query_counter = 1
		portal_types = ["placeholder"]
		type_override = None
		while query_counter <= portal_counter:
			if type_override is not None:
				query_portal = str(type_override)
			else:
				query_portal = input("Specify type for portal #" + str(query_counter) + ": ")
			if query_portal.endswith("+"):
				query_portal = query_portal.replace("+", "")
				type_override = int(query_portal)
			if query_portal == "list":
				for c in choices:
					print(str(c["val"]) + " - " + c["desc"])
				print()
			elif query_portal == "r":
				query_counter -= 1
				query_counter = max(1, query_counter)
			else:
				try:
					query_portal = int(query_portal)
					choice_match = False
					for c in choices:
						if query_portal == c["val"]:
							portal_types.insert(query_counter, c)
							choice_match = True
					if choice_match:
						query_counter += 1
					else:
						print("'" + str(query_portal) + "' is invalid. Choose a number between 1 and " + str(len(choices)) + ".")
						type_override = None
				except ValueError:
					print("'" + query_portal + "' is invalid. Must be a number, 'list', or 'r'. Try again.")

	portal_counter = 1
	for portal in data["portals"]:
		if args.refine_portals:
			try:
				portal_type = portal_types[portal_counter]["name"]
			except NameError:
				portal_type = "door"
		else:
			portal_type = "door"
		portal_counter += 1
		if portal_type != "passage":
			occluder_points = spos_x(portal["bounds"][0]["x"]) + "," + spos_y(portal["bounds"][0]["y"]) + "," + spos_x(portal["bounds"][1]["x"]) + "," + spos_y(portal["bounds"][1]["y"])
			if portal_type != "toggleable_wall" and portal_type != "illusory_wall":
				expand_points = expand_line(pos_x(portal["bounds"][0]["x"]), pos_y(portal["bounds"][0]["y"]), pos_x(portal["bounds"][1]["x"]), pos_y(portal["bounds"][1]["y"]), args.door_width)
				occluder_points = str(expand_points[0]["x"]) + "," + str(expand_points[0]["y"]) + "," + str(expand_points[1]["x"]) + "," + str(expand_points[1]["y"]) + "," + str(expand_points[2]["x"]) + "," + str(expand_points[2]["y"]) + "," + str(expand_points[3]["x"]) + "," + str(expand_points[3]["y"])
			occluders.append({ "points": occluder_points, "type": portal_type })

	lights = []
	if data["lights"].__len__() > 0:
		for light in data["lights"]:
			lights.append({ "x": pos_x(light["position"]["x"]), "y": pos_y(light["position"]["y"]), "color": light["color"], "range": light["range"] })

	offset_x = pos_x(data["resolution"]["map_size"]["x"]) / 2 # This is correct! Don't touch!
	offset_y = pos_y((data["resolution"]["map_size"]["y"]) / 2)
	images.append(fg_module.generate_image("images/" + filename + ".png", filename, ".png", pixels_per_grid, args.grid_color, occluders, offset_x, offset_y, lights))
	counter += 1

library = SubElement(xml_client_root, "library")
module = SubElement(library, module_id, { "static": "true" })
SubElement(module, "categoryname", { "type": "string" })
SubElement(module, "name", { "type": "string" }).text = module_id
entries = SubElement(module, "entries")
icon = SubElement(entries, "image", { "static": "true" })
librarylink = SubElement(icon, "librarylink", { "type": "windowreference" })
SubElement(librarylink, "class").text = "reference_list"
SubElement(librarylink, "recordname").text = ".."
SubElement(icon, "name", { "type": "string" }).text = "Images"
SubElement(icon, "recordtype", { "type": "string" }).text = "image"
SubElement(xml_client_root, "reference", { "static": "true" })

with open("client.xml", 'wb') as f:
	f.write(bytes(xml_version, "utf8") + tostring(xml_client_root))
to_zip.append("client.xml")

xml_definition_root = Element("root", xml_data_version)
SubElement(xml_definition_root, "name").text = module_name
SubElement(xml_definition_root, "category")
SubElement(xml_definition_root, "author").text = args.author
SubElement(xml_definition_root, "ruleset").text = "5E"

with open("definition.xml", 'wb') as f:
	f.write(bytes(xml_version, "utf8") + tostring(xml_definition_root))
to_zip.append("definition.xml")

zip_file = ZipFile(module_id + "." + args.extension, "w")
for f in to_zip:
	zip_file.write(f)
zip_file.close()

if counter > 0:
	s = "s"
	if counter == 1:
		s = ""
	if args.verbose:
		print("Finished processing (" + str(counter) + " file" + s + ")")
	print(module_id + "." + args.extension)
else:
	if args.verbose:
		print("No files were processed!")
