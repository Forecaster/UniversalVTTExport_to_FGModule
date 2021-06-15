#!/usr/bin/env

# Provide a desired module name as the first argument
# Provide any number of Universal VTT json files as individual arguments after that
# Each provided file will be included in the module as a map

from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile
import argparse
import base64
import json
import sys
import os
import re

import fg_module_testb as fg_module
import utilib

verbose=False
def vprint(msg):
	if verbose:
		print(msg)

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

def main(module_name, files, refine_portals=False, door_width=10, grid_color="00000000", author="DungeonFog", extension="mod", cleanup=True, extract=False):
	try:
		from PIL import Image, ImageFont, ImageDraw, ImageEnhance
	except ImportError:
		if refine_portals:
			sys.stdout = sys.__stdout__
			print("Import error. Unable to load Pillow module. This is required to use refine portals. Either run without -p or install the required module.")
			sys.exit()

	if extract:
		vprint("Extraction mode enabled!")

	to_zip = []
	used_image_names = []
	module_id = module_name.replace(" ", "_").lower()

	xml_version = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
	xml_data_version = { "version": "4.1", "dataversion": "20210302", "release": "8.1|CoreRPG:4.1" }
	xml_client_root = Element("root", xml_data_version)
	images = SubElement(xml_client_root, "image")

	cleanup = []
	counter = 0
	for file in files:
		json_str = None
		data = None
		vprint("Processing file: " + file)
		with open(file) as f:
			json_str = f.read()
		data = json.loads(json_str)
		pixels_per_grid = data["resolution"]["pixels_per_grid"]
		global_grid_size = pixels_per_grid

		imgstring = data['image']

		imgdata = base64.b64decode(imgstring)
		exp = re.compile("(.*\/)?(.*?)(\..{2,6})")
		match = exp.match(file)
		path = match.group(1)
		filename = match.group(2)
		ext = match.group(3)
		filename_counter = 0
		while used_image_names.__contains__(filename + ext):
			filename_counter += 1
			filename = match.group(1) + "_" + str(filename_counter)
		used_image_names.append(filename + ext)
		try:
			os.mkdir("images")
		except FileExistsError:
			pass
		with open("images/" + filename + ".png", 'wb') as f:
			f.write(imgdata)
		to_zip.append("images/" + filename + ".png")
		if extract:
			break

		occluders = []
		for los in data["line_of_sight"]:
			occluders.append({ "points": spos_x(los[0]["x"]) + "," + spos_y(los[0]["y"]) + "," + spos_x(los[1]["x"]) + "," + spos_y(los[1]["y"]), "type": "wall" })

		portal_types = ["placeholder"]
		if refine_portals:
			source_img = Image.open("images/" + filename + ".png").convert("RGBA")
			draw = ImageDraw.Draw(source_img)
			portal_counter = 0
			font = ImageFont.truetype("arial.ttf", 14)
			for portal in data["portals"]:
				portal_counter += 1
				draw.text((portal["bounds"][0]["x"] * global_grid_size, portal["bounds"][0]["y"] * global_grid_size), str(portal_counter), font=font, stroke_width=4, stroke_fill=(0,0,0))
			image_path = filename + "_portals.png"
			source_img.save(image_path, "PNG")
			cleanup.append(image_path)

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

			def get_choice_by_value(value: int):
				for c in choices:
					if value == c["val"]:
						return c
				return None

			def get_choice_by_name(name: str):
				for c in choices:
					if name == c["name"]:
						return c
				return None

			query_counter = 1
			type_override = None
			while query_counter <= portal_counter:
				if type_override is not None:
					query_portal = str(type_override)
				else:
					query_portal = query_input("Specify type for portal #" + str(query_counter) + ": ")
				if query_portal.startswith("portallist;"):
					query_portal = query_portal.split(";")[1:]
					for p in query_portal:
						portal_types.append(get_choice_by_name(p.lower()))
					print(portal_types)
					break
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
						choice_match = get_choice_by_value(query_portal)
						if choice_match:
							portal_types.insert(query_counter, choice_match)
							query_counter += 1
						else:
							print("'" + str(query_portal) + "' is invalid. Choose a number between 1 and " + str(len(choices)) + ".")
							type_override = None
					except ValueError:
						print("'" + query_portal + "' is invalid. Must be a number, 'list', or 'r'. Try again.")

		portal_counter = 1
		for portal in data["portals"]:
			if refine_portals:
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
					expand_points = utilib.expand_line(pos_x(portal["bounds"][0]["x"]), pos_y(portal["bounds"][0]["y"]), pos_x(portal["bounds"][1]["x"]), pos_y(portal["bounds"][1]["y"]), door_width)
					occluder_points = str(expand_points[0]["x"]) + "," + str(expand_points[0]["y"]) + "," + str(expand_points[1]["x"]) + "," + str(expand_points[1]["y"]) + "," + str(expand_points[2]["x"]) + "," + str(expand_points[2]["y"]) + "," + str(expand_points[3]["x"]) + "," + str(expand_points[3]["y"])
				occluders.append({ "points": occluder_points, "type": portal_type })

		lights = []
		if data["lights"].__len__() > 0:
			for light in data["lights"]:
				lights.append({ "x": pos_x(light["position"]["x"]), "y": pos_y(light["position"]["y"]), "color": light["color"], "range": light["range"] })

		offset_x = pos_x(data["resolution"]["map_size"]["x"]) / 2 # This is correct! Don't touch!
		offset_y = pos_y((data["resolution"]["map_size"]["y"]) / 2)
		image_path = "images/" + filename + ".png"
		images.append(fg_module.generate_image(image_path, filename, ".png", pixels_per_grid, grid_color, occluders, offset_x, offset_y, lights))
		cleanup.append(image_path)
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
	cleanup.append("client.xml")

	xml_definition_root = Element("root", xml_data_version)
	SubElement(xml_definition_root, "name").text = module_name
	SubElement(xml_definition_root, "category")
	SubElement(xml_definition_root, "author").text = author
	SubElement(xml_definition_root, "ruleset").text = "5E"

	with open("definition.xml", 'wb') as f:
		f.write(bytes(xml_version, "utf8") + tostring(xml_definition_root))
	to_zip.append("definition.xml")
	cleanup.append("definition.xml")

	zip_file = ZipFile(module_id + "." + extension, "w")
	for f in to_zip:
		zip_file.write(f)
	zip_file.close()

	if counter > 0:
		s = "s"
		if counter == 1:
			s = ""
		vprint("Finished processing (" + str(counter) + " file" + s + ")")
	else:
		vprint("No files were processed!")

	if cleanup:
		vprint("Cleaning up working directory...")
		for path in cleanup:
			vprint("Deleting '" + path + "'")
			os.remove(path)
		vprint("Deleting 'images' dir")
		try:
			os.rmdir("images")
		except OSError:
			print("Skipped removing image directory because it contains other files.")
	else:
		vprint("Skipped cleanup due to arguments")
	print(module_id + "." + extension)

name = "DungeonFog FG Module Generator"
version = "v1.1"

def get_argparse():
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
	parser.add_argument('-c', dest='cleanup', action='store_false', help="By default the script cleans up created files at the end of the process except the generated module. This argument disables cleanup.")
	parser.add_argument('-x', dest='extract', action='store_true', help="Only extracts the image embedded in the provided df2vtt file then exits.")
	return parser

query_input = input

def do_args(args):
	arg_parser = get_argparse()
	args = arg_parser.parse_args(args)

	verbose = args.verbose
	main(args.module_name[0], args.files, refine_portals=args.refine_portals, door_width=args.door_width, grid_color=args.grid_color, author=args.author, extension=args.extension, cleanup=args.cleanup, extract=args.extract)

if __name__ == '__main__':
	do_args(sys.argv)
