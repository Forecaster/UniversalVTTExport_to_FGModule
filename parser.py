# Provide a desired module name as the first argument
# Provide any number of Universal VTT json files as individual arguments after that
# Each provided file will be included in the module as a map

from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile
from sys import argv
import argparse
import base64
import json
import math
import os
import re

parser = argparse.ArgumentParser(description="Converts one or more df2vtt files into a Fantasy Grounds module")
parser.add_argument('module_name', metavar='M', type=str, nargs=1, help="The name for the output module")
parser.add_argument('files', metavar='F', type=str, nargs='+', help="The df2vtt files to parse into a module")
parser.add_argument('-a', dest='author', default='DungeonFog', type=str, help="Specify the module author (Default: DungeonFog)")
parser.add_argument('-w', dest='wall_width', default=10, type=int, help="Specify wall width (Default: 10)")

args = parser.parse_args()

enable_zero_occluder = True

if argv.__len__() == 1:
	print("No module name provided.")
	exit()
elif argv[1] == "workdir":
	print("Workdir: " + os.getcwd())
	exit()

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

image_id = 1
def generate_image(fn, name, img_ext, grid_size, img_occluders=None, img_offset_x = 0, img_offset_y = 0):
	if img_occluders is None:
		img_occluders = []
	global image_id
	img = Element("id-" + str(image_id).zfill(5))
	SubElement(img, "locked", { "type": "number" }).text = "0"
	SubElement(img, "name", { "type": "string" }).text = name
	image = SubElement(img, "image", { "type": "image" })
	SubElement(image, "grid").text = "on"
	SubElement(image, "gridsize").text = str(grid_size) + "," + str(grid_size)
	SubElement(image, "gridoffset").text = "0,0"
	SubElement(image, "gridsnap").text = "on"
	# SubElement(image, "color").text = "#00FFFFFF" # transparent
	SubElement(image, "color").text = "#FF0F00AF" # blue visible
	layers = SubElement(image, "layers")

	layer = SubElement(layers, "layer")
	SubElement(layer, "name").text = name + img_ext
	SubElement(layer, "id").text = "0"
	SubElement(layer, "type").text = "image"
	SubElement(layer, "bitmap").text = fn
	SubElement(layer, "matrix").text = "1,0,0,0,0,1,0,0,0,0,1,0," + str(img_offset_x) + "," + str(img_offset_y) + ",0,1"

	img_xml_occluders = SubElement(layer, "occluders")
	for occ in img_occluders:
		img_xml_occluders.append(generate_simple_occluder(occ["points"], occ["type"]))

	image_id += 1
	return img

occluder_id = 0
def generate_occluder(points, toggleable = False, single_sided = False, closed = True, allow_vision = False, counterclockwise = False):
	global occluder_id
	occluder = Element("occluder")
	SubElement(occluder, "id").text = str(occluder_id)
	occluder_id += 1
	SubElement(occluder, "points").text = points
	if toggleable:
		SubElement(occluder, "toggleable")
		if closed:
			SubElement(occluder, "closed")
	if single_sided:
		SubElement(occluder, "single_sided")
	if allow_vision:
		SubElement(occluder, "allow_vision")
	if counterclockwise:
		SubElement(occluder, "counterclockwise")
	return occluder

def generate_simple_occluder(points, occluder_type = None):
	if occluder_type is None:
		occluder_type = "wall"
	if occluder_type == "door":
		return generate_occluder(points, True, True, True, False, True)
	elif occluder_type == "window":
		return generate_occluder(points, True, False, True, True)
	return generate_occluder(points)

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
	dx = x1 - x0 #delta x
	dy = y1 - y0 #delta y
	line_length = math.sqrt(dx * dx + dy * dy)
	dx /= line_length
	dy /= line_length
	#Ok, (dx, dy) is now a unit vector pointing in the direction of the line
	#A perpendicular vector is given by (-dy, dx)
	px = 0.5 * t * (-dy) #perpendicular vector with length thickness * 0.5
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
module_name = argv[1]
module_id = module_name.replace(" ", "_").lower()
counter = 0

xml_version = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
xml_data_version = { "version": "4.1", "dataversion": "20210302", "release": "8.1|CoreRPG:4.1" }
xml_client_root = Element("root", xml_data_version)
images = SubElement(xml_client_root, "image")

for arg in argv:
	json_str = None
	data = None
	if counter > 1:
		print("Export file: " + arg)
		with open(arg) as f:
			json_str = f.read()
		data = json.loads(json_str)
		pixels_per_grid = data["resolution"]["pixels_per_grid"]
		global_grid_size = pixels_per_grid

		imgstring = data['image']

		imgdata = base64.b64decode(imgstring)
		exp = re.compile("(.*)(\..{2,6})")
		match = exp.match(arg)
		filename = match[1]
		ext = match[2]
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
		for portal in data["portals"]:
			eport = expand_line(pos_x(portal["bounds"][0]["x"]), pos_y(portal["bounds"][0]["y"]), pos_x(portal["bounds"][1]["x"]), pos_y(portal["bounds"][1]["y"]), args.wall_width)
			occluders.append({ "points": str(eport[0]["x"]) + "," + str(eport[0]["y"]) + "," + str(eport[1]["x"]) + "," + str(eport[1]["y"]) + "," + str(eport[2]["x"]) + "," + str(eport[2]["y"]) + "," + str(eport[3]["x"]) + "," + str(eport[3]["y"]), "type": "door" })
		offset_x = pos_x(data["resolution"]["map_size"]["x"]) / 2 #This is correct! Don't touch!
		offset_y = pos_y((data["resolution"]["map_size"]["y"]) / 2)
		images.append(generate_image("images/" + filename + ".png", filename, ".png", pixels_per_grid, occluders, offset_x, offset_y))

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

zip_file = ZipFile(module_id + ".mod", "w")
for f in to_zip:
	zip_file.write(f)
zip_file.close()

print("Finished processing")