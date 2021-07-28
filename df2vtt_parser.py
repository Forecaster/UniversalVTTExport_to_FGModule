#!/usr/bin/env

# Provide a desired module name as the first argument
# Provide any number of Universal VTT json files as individual arguments after that
# Each provided file will be included in the module as a map

from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile
import traceback
import datetime
import argparse
import base64
import json
import sys
import os
import re

import fg_module
import utilib

name = "DungeonFog FG Module Generator"
version = "v1.2.2"

log_levels = {
	"fatal": "fatal",
	"trace": "trace",
	"error": "error",
	"warn": "warn",
	"info": "info",
	"debug": "debug",
}

log_level_ranks = {
	'debug': 0,
	'info': 1,
	'warn': 2,
	'error': 3,
	'trace': 4,
	'fatal': 5,
}

log_level = log_levels['warn']
log_file = False

def vprint(msg, level = 'info', log_file_override = None):
	global log_level, log_file, log_level_ranks
	if type(msg) != str:
		msg = str(msg)
	if level == 'init' or log_level_ranks[level] >= log_level_ranks[log_level]:
		print("[" + level.upper() + "] " + msg)
		if (log_file_override is not None and log_file_override) or log_file:
			with open("output.log", "a") as f:
				f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " [" + level.upper() + "] " + msg + "\n")

global_grid_size = 50
portal_count_output = 0
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

options_default = {
	"log_level": log_level,
	"log_to_file": log_file,
	"refine_portals": False,
	"door_width": 10,
	"grid_color": "00000000",
	"author": "DungeonFog",
	"extension": "mod",
	"do_cleanup": True,
	"extract": False,
	"test_occluder": False,
	"ignore_lights": False,
	"ignore_occluders": False,
	"grid_size_real": 5,
	"test_image": False,
	"test_image_textless": False,
	"portal_intersect_fix_enabled": True,
	"portal_refine_output_override": False
}

def main(module_name, files, options = None):
	global global_grid_size, options_default, log_level, log_file, portal_count_output

	if options is None:
		options = options_default
	else:
		keys = options.keys()
		for key in options_default.keys():
			if not keys.__contains__(key):
				options[key] = options_default[key]

	vprint("Options:", 'debug')
	vprint(str(options), 'debug')

	if options.get('log_level'):
		log_level = options['log_level']

	if options.get('log_to_file'):
		log_file = options['log_to_file']

	vprint("Log level: " + str(log_level_ranks[log_level]) + ": " + log_level, 'init')
	if log_file:
		vprint("Logging output to 'output.log'", 'init')

	try:
		from PIL import Image, ImageFont, ImageDraw, ImageEnhance, ImageColor
	except ImportError:
		if options['refine_portals']:
			vprint("Import error. Unable to load Pillow module. This is required to use refine portals. Either run without -p or install the required module.", 'error')
			vprint(traceback.format_exc(), 'trace')
			sys.exit(1)
		if options['test_image']:
			vprint("Import error. Unable to load Pillow module. This is required to generate test image. Either run without -p or install the required module.", 'error')
			vprint(traceback.format_exc(), 'trace')
			sys.exit(1)
	try:
		import shapely
	except ImportError:
		if not options['ignore_lights']:
			vprint("Import error. Unable to load Shapely module. This is required to process lights and fix intersecting walls.", 'error')
			vprint(traceback.format_exc(), 'trace')
			sys.exit(1)

	if options['extract']:
		vprint("Extraction mode enabled!", 'info')

	to_zip = []
	used_image_names = []
	module_id = module_name.replace(" ", "_").lower()

	xml_version = "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
	xml_data_version = { "version": "4.1", "dataversion": "20210302", "release": "8.1|CoreRPG:4.1" }
	xml_client_root = Element("root", xml_data_version)
	images = SubElement(xml_client_root, "image")

	cleanup = []
	counter = 0
	successfully_processed = 0
	for file in files:
		try:
			json_str = None
			data = None
			vprint("Processing file: " + file, 'info')
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
			if options['extract']:
				break

			occluders_walls = []
			occluders_portals = []
			if not options['ignore_occluders']:
				if options['test_occluder']:
					occluders_walls.append({ "points" : spos_x(0) + "," + spos_y(0) + "," + spos_x(1) + "," + spos_y(1), "type": "wall" })

				for los in data["line_of_sight"]:
					occluders_walls.append({ "points": spos_x(los[0]["x"]) + "," + spos_y(los[0]["y"]) + "," + spos_x(los[1]["x"]) + "," + spos_y(los[1]["y"]), "type": "wall" })

				portal_types = ["placeholder"]
				if options['refine_portals']:
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
						{ "val": 1, "name": "door", 						"expand": True, "desc": "Door: Blocks path & LOS when closed."},
						{ "val": 2, "name": "window",						"expand": True, "desc": "Window: Blocks path when closed, never blocks LOS."},
						{ "val": 3, "name": "passage",		 			"expand": True, "desc": "Passage: Leaves gap in wall."},
						{ "val": 4, "name": "toggleable_wall", 	"expand": True, "desc": "Toggleable Wall: Like a door, but flush with the wall."},
						{ "val": 5, "name": "illusory_wall",		"expand": True, "desc": "Illusory Wall: - Blocks LOS, never blocks path, cannot be toggled."},
					]

					vprint("Refining " + str(portal_counter) + " portals in '" + filename + '_portals.png', 'info')
					if options["portal_refine_output_override"] is None:
						print("A total of " + str(portal_counter) + " portals were found, these have been numbered in the file " + filename + "_portals.png in the working directory. Open this file and specify the desired type for each portal choosing from the following:")
						for c in choices:
							print(str(c["val"]) + " - " + c["desc"])
						print()
						print("list - If you wish to see this list again type 'list' instead of the type number.")
						print("1+ - You can enter a choice followed by + (ex: 2+) to set all remaining portals to that type.")
						print("r - If you enter the wrong type you can type 'r' to go back one step. You can keep doing this to go back to the beginning if you want.")
						print()
					else:
						portal_count_output = portal_counter

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
					portal_key = ["portallist"]
					while query_counter <= portal_counter:
						if type_override is not None:
							query_portal = str(type_override)
						else:
							query_portal = query_input("Specify type for portal #" + str(query_counter) + ": ")
						if query_portal.startswith("portallist;"):
							vprint("Portal refinement GUI override mode!", 'debug')
							query_portal = query_portal.split(";")[1:]
							# print(query_portal)
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
									portal_key.append(choice_match["name"])
									query_counter += 1
								else:
									print("'" + str(query_portal) + "' is invalid. Choose a number between 1 and " + str(len(choices)) + ".")
									type_override = None
							except ValueError:
								print("'" + query_portal + "' is invalid. Must be a number, 'list', or 'r'. Try again.")
					if len(portal_key) > 1:
						print("If you need to generate this module again with the same portals you can paste this key into the portal 1 prompt: ", ";".join(portal_key))

				portal_counter = 1
				for portal in data["portals"]:
					if options['refine_portals']:
						try:
							portal_type = portal_types[portal_counter]["name"]
						except Exception:
							vprint("No value for portal " + str(portal_counter) + " found. Assumed door.", 'debug')
							portal_type = "door"
					else:
						portal_type = "door"
					portal_counter += 1
					if portal_type != "passage":
						occluder_points = spos_x(portal["bounds"][0]["x"]) + "," + spos_y(portal["bounds"][0]["y"]) + "," + spos_x(portal["bounds"][1]["x"]) + "," + spos_y(portal["bounds"][1]["y"])
						if portal_type != "toggleable_wall" and portal_type != "illusory_wall":
							line = ((pos_x(portal["bounds"][0]["x"]), pos_y(portal["bounds"][0]["y"])), (pos_x(portal["bounds"][1]["x"]), pos_y(portal["bounds"][1]["y"])))
							expand_points = utilib.expand_line(line, options['door_width'])
							occluder_points = ",".join(utilib.tuple_to_point_list(expand_points, True))
						occluders_portals.append({ "points": occluder_points, "type": portal_type })

			# Concealed door detection & fixing
			if options['portal_intersect_fix_enabled']:
				for pkey, portal in enumerate(occluders_portals):
					new_segments = []
					portal_points = portal["points"].split(",")
					portal_line = ((float(portal_points[0]), float(portal_points[1])), (float(portal_points[2]), float(portal_points[3])))
					# print("portal_line", portal_line)
					# print(portal["type"])
					# print(portal_points)
					flat_portal = False
					if portal["type"] == "illusory_wall" or portal["type"] == "toggleable_wall":
						flat_portal = True
						expanded = utilib.expand_line(portal_line, 10)
						# print(expanded)
						portal_points = [ str(expanded[0][0]), str(expanded[0][1]), str(expanded[1][0]), str(expanded[1][1]), str(expanded[2][0]), str(expanded[2][1]), str(expanded[3][0]), str(expanded[3][1]) ]
					portal_polygon = ((float(portal_points[0]), float(portal_points[1])), (float(portal_points[2]), float(portal_points[3])), (float(portal_points[4]), float(portal_points[5])), (float(portal_points[6]), float(portal_points[7])))
					p_seg_1 = (portal_polygon[0], portal_polygon[1])
					p_seg_2 = (portal_polygon[1], portal_polygon[2])
					p_seg_3 = (portal_polygon[2], portal_polygon[3])
					p_seg_4 = (portal_polygon[3], portal_polygon[0])

					intersects = []
					deletes = []
					wall_index_counter = 0
					replace_index = None
					for wall in occluders_walls:
						# print("Test wall " + str(wall_index_counter))
						wall_points = wall["points"].split(",")
						wall_segment = ( (float(wall_points[0]), float(wall_points[1])), (float(wall_points[2]), float(wall_points[3])) )
						# print("Segment", wall_segment)

						point_0_inside = utilib.check_point_is_inside_polygon(wall_segment[0], portal_polygon)
						point_1_inside = utilib.check_point_is_inside_polygon(wall_segment[1], portal_polygon)

						if point_0_inside and point_1_inside: # 2 Wall points are within portal polygon: delete wall completely
							# print("Delete wall " + str(wall_index_counter))
							deletes.append(wall_index_counter)
						elif point_0_inside: # 1 Wall point is within portal polygon: remove part of wall segment inside polygon at intersection
							inter = utilib.get_polygon_intersect_points(wall_segment, portal_polygon)[0]
							# print("inter", inter)
							# print("point_0_inside", inter)
							# print("Replace wall " + str(wall_index_counter), occluders_walls[wall_index_counter])
							occluders_walls[wall_index_counter] = { "points": str(inter[0]) + "," + str(inter[1]) + "," + str(wall_segment[1][0]) + "," + str(wall_segment[1][1]), "type": "wall" }
							if flat_portal:
								distance_0 = utilib.distance(inter, portal_line[0])
								distance_1 = utilib.distance(inter, portal_line[1])
								# print("distance", distance_0, distance_1)
								if distance_0 < distance_1:
									portal_line = ( inter, portal_line[1] )
									portal_points = utilib.tuple_to_point_list(portal_line, True)
									occluders_portals[pkey]["points"] = ",".join(portal_points)
								else:
									portal_line = ( portal_line[0], inter )
									portal_points = utilib.tuple_to_point_list(portal_line, True)
									occluders_portals[pkey]["points"] = ",".join(portal_points)
							# print(occluders_walls[wall_index_counter])
						elif point_1_inside: # Same as previous, but with wall point 1
							inter = utilib.get_polygon_intersect_points(wall_segment, portal_polygon)[0]
							# print("inter", inter)
							# print("point_1_inside", inter)
							# print("Replace wall " + str(wall_index_counter), occluders_walls[wall_index_counter])
							occluders_walls[wall_index_counter] = { "points": str(wall_segment[0][0]) + "," + str(wall_segment[0][1]) + "," + str(inter[0]) + "," + str(inter[1]), "type": "wall" }
							if flat_portal:
								distance_0 = utilib.distance(inter, portal_line[0])
								distance_1 = utilib.distance(inter, portal_line[1])
								# print("distance", distance_0, distance_1)
								if distance_0 < distance_1:
									portal_line = ( inter, portal_line[1] )
									portal_points = utilib.tuple_to_point_list(portal_line, True)
									occluders_portals[pkey]["points"] = ",".join(portal_points)
								else:
									portal_line = ( portal_line[0], inter )
									portal_points = utilib.tuple_to_point_list(portal_line, True)
									occluders_portals[pkey]["points"] = ",".join(portal_points)
							# print(occluders_walls[wall_index_counter])
						else: # No wall points are within portal polygon: check if wall intersects with portal polygon
							ints = []
							if utilib.intersects(p_seg_1, wall_segment):
								# print("Seg 1 intersect!")
								i = utilib.get_intersect_point(p_seg_1, wall_segment)
								if utilib.true_intersect_check(p_seg_1, wall_segment, i):
									ints.append(i)
							if utilib.intersects(p_seg_2, wall_segment):
								# print("Seg 2 intersect!")
								i = utilib.get_intersect_point(p_seg_2, wall_segment)
								if utilib.true_intersect_check(p_seg_2, wall_segment, i):
									ints.append(i)
							if utilib.intersects(p_seg_3, wall_segment):
								# print("Seg 3 intersect!")
								i = utilib.get_intersect_point(p_seg_3, wall_segment)
								if utilib.true_intersect_check(p_seg_3, wall_segment, i):
									ints.append(i)
							if utilib.intersects(p_seg_4, wall_segment):
								# print("Seg 4 intersect!")
								i = utilib.get_intersect_point(p_seg_4, wall_segment)
								if utilib.true_intersect_check(p_seg_4, wall_segment, i):
									ints.append(i)
							if len(ints) > 1:
								replace_index = wall_index_counter
								intersects.append({ "wall": wall_segment, "points": ints })
						wall_index_counter += 1

					# print(intersects)
					for i in intersects:
						point_count = 0
						if len(i["points"]) > 1:
							for w in i["wall"]:
								# print("Testing wall " + str(w) + " vs intersect points 0: " + str(i["points"][0]) + " and 1: " + str(i["points"][1]))
								d0 = utilib.distance(w, i["points"][0])
								# print("Distance to 0: " + str(d0))
								d1 = utilib.distance(w, i["points"][1])
								# print("Distance to 1: " + str(d1))
								if d0 < d1:
									new_segments.append(( w, i["points"][0] ))
								else:
									new_segments.append(( w, i["points"][1] ))

					if replace_index is not None:
						occluders_walls.pop(replace_index)
						for s in new_segments:
							# print(s)
							occluders_walls.append({ "points": str(s[0][0]) + "," + str(s[0][1]) + "," + str(s[1][0]) + "," + str(s[1][1]), "type": "wall" })

					for delete in deletes:
						occluders_walls[delete] = "delete"

					del_count = 0
					for key, wall in enumerate(occluders_walls):
						if wall == "delete":
							del_count += 1

					for i in range(del_count):
						for key, val in enumerate(occluders_walls):
							if val == "delete":
								occluders_walls.pop(key)
								break

			lights = []
			if not options['ignore_lights']:
				if data["lights"].__len__() > 0:
					for light in data["lights"]:
						lights.append({ "x": pos_x(light["position"]["x"]), "y": pos_y(light["position"]["y"]), "color": light["color"], "range_tiles": light["range"], "range_pixels": light["range"] * pixels_per_grid, "range_real": light["range"] * options['grid_size_real']})
			else:
				vprint("Ignoring lights")

			occluders = occluders_walls + occluders_portals
			offset_x = pos_x(data["resolution"]["map_size"]["x"]) / 2 # This is correct! Don't touch!
			offset_y = pos_y((data["resolution"]["map_size"]["y"]) / 2)
			image_path = "images/" + filename + ".png"
			images.append(fg_module.generate_image(image_path, filename, ".png", pixels_per_grid, options['grid_color'], occluders, offset_x, offset_y, lights))
			cleanup.append(image_path)
			counter += 1

			if options['test_image'] or options['test_image_textless']:
				font = ImageFont.truetype("arial.ttf", 8)
				wall_color = (255,0,0)
				source_img = Image.open("images/" + filename + ".png").convert("RGBA")
				draw = ImageDraw.Draw(source_img)
				counter_walls = -1
				counter_portals = -1
				for occluder in occluders:
					points = occluder["points"].split(",")
					square = False
					if occluder["type"] == "wall":
						if wall_color == (255,0,0):
							wall_color = (255,150,150)
						else:
							wall_color = (255,0,0)
						counter_walls += 1
					else:
						counter_portals += 1

					color = wall_color
					if occluder["type"] == "door":
						color = (0,0,255)
						square = True
					elif occluder["type"] == "window":
						color = (0,255,255)
						square = True
					elif occluder["type"] == "passage":
						color = (0,0,0,0)
					elif occluder["type"] == "toggleable_wall":
						color = (255,255,0)
					elif occluder["type"] == "illusory_wall":
						color = (0,170,0)
						square = True
					x0 = float(points[0])
					y0 = -float(points[1])
					if not square:
						x1 = float(points[2])
						y1 = -float(points[3])
					else:
						x1 = float(points[4])
						y1 = -float(points[5])
					offs = 20
					if square:
						draw.line([float(points[0]), -float(points[1]), float(points[2]), -float(points[3])], fill=color, width=2)
						draw.line([float(points[2]), -float(points[3]), float(points[4]), -float(points[5])], fill=color, width=2)
						draw.line([float(points[4]), -float(points[5]), float(points[6]), -float(points[7])], fill=color, width=2)
						draw.line([float(points[6]), -float(points[7]), float(points[0]), -float(points[1])], fill=color, width=2)
						# if not options['test_image_textless']:
						# 	draw.text([((x1 - x0) / 3) + x0 - offs, ((y1 - y0) / 3) + y0 - offs], "p" + str(counter_portals), stroke_fill=(0,0,0), stroke_width=2, font=font)
					else:
						draw.line([x0, y0, x1, y1], fill=color, width=4)
						if not options['test_image_textless']:
							draw.text([((x1 - x0) / 3) + x0 - offs, ((y1 - y0) / 3) + y0 - offs], "w" + str(counter_walls), stroke_fill=(0,0,0), stroke_width=2, font=font)

				for light in lights:
					x0 = light["x"] - 5
					y0 = -light["y"] - 5
					x1 = light["x"] + 5
					y1 = -light["y"] + 5
					draw.ellipse([x0, y0, x1, y1], fill=(216, 0, 255))
					points = fg_module.generate_light_radius_points(light["x"], light["y"], light["range_pixels"])
					for p in points:
						x0 = p[0] - 2
						y0 = -p[1] - 2
						x1 = p[0] + 2
						y1 = -p[1] + 2
						draw.ellipse([x0, y0, x1, y1], fill=(255,255,255))
					points = fg_module.generate_light_radius_points(light["x"], light["y"], light["range_pixels"] * 2)
					for p in points:
						x0 = p[0] - 2
						y0 = -p[1] - 2
						x1 = p[0] + 2
						y1 = -p[1] + 2
						draw.ellipse([x0, y0, x1, y1], fill=(0,0,0))
				source_img.save(filename + "_test_image.png", "PNG")
			successfully_processed += 1
		except FileNotFoundError:
			vprint("An error occurred when opening the file '" + file + "'. It will be skipped.", 'error')
		except Exception as exception:
			vprint("An unexpected error occurred when opening the file '" + file + "'. It will be skipped.", 'error')
			vprint(type(exception).__name__ + " - " + str(exception), 'trace')
			vprint(traceback.format_exc(), 'trace')

	if successfully_processed == 0:
		vprint("No files were successfully processed. No module will be generated.", 'fatal')
		exit(0)

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

	with open("db.xml", 'wb') as f:
		f.write(bytes(xml_version, "utf8") + tostring(xml_client_root))
	to_zip.append("db.xml")
	cleanup.append("db.xml")

	xml_definition_root = Element("root", xml_data_version)
	SubElement(xml_definition_root, "name").text = module_name
	SubElement(xml_definition_root, "category")
	SubElement(xml_definition_root, "author").text = options['author']
	SubElement(xml_definition_root, "ruleset").text = "5E"

	with open("definition.xml", 'wb') as f:
		f.write(bytes(xml_version, "utf8") + tostring(xml_definition_root))
	to_zip.append("definition.xml")
	cleanup.append("definition.xml")

	zip_file = ZipFile(module_id + "." + options['extension'], "w")
	for f in to_zip:
		zip_file.write(f)
	zip_file.close()

	if counter > 0:
		s = "s"
		if counter == 1:
			s = ""
		vprint("Finished processing (" + str(counter) + " file" + s + ")", 'info')
	else:
		vprint("No files were processed!", 'warn')

	if options['do_cleanup']:
		vprint("Cleaning up working directory...", 'info')
		for path in cleanup:
			vprint("Deleting '" + path + "'", 'debug')
			os.remove(path)
		vprint("Deleting 'images' dir", 'debug')
		try:
			os.rmdir("images")
		except OSError:
			vprint("Skipped removing image directory because it contains other files.", 'warn')
	else:
		vprint("Skipped cleanup due to arguments", 'info')
	print(module_id + "." + options['extension'])

def get_argparse():
	parser = argparse.ArgumentParser(description=name + " " + version + " - Converts one or more df2vtt files into a Fantasy Grounds module.")
	parser.add_argument('module_name', metavar='M', type=str, help="The module name as shown within Fantasy Grounds. Also used as the filename.")
	parser.add_argument('files', metavar='F', nargs='+', help="One or more paths to df2vtt files to parse into a module.")
	parser.add_argument('-a', dest='author', default='DungeonFog', help="Set a custom module author. (Default: DungeonFog)")
	parser.add_argument('-d', dest='door_width', default=10, type=int, nargs=1, help="Specify door width. (Default: 10)")
	parser.add_argument('-v', dest='log_level', help="The log level to use. Options are " + ", ".join(log_levels) + ". Default: " + log_level)
	parser.add_argument('-e', dest='extension', default='mod', help="The desired file name extension for the output module file (eg. zip). (Default: mod)")
	parser.add_argument('-g', dest='grid_color', default='00000000', help="The grid color. (Default: 00000000)")
	parser.add_argument('--version', action='version', version=name + ' ' + version)
	parser.add_argument('-p', dest='refine_portals', action='store_true', help="Whether to refine portals (doors) and define types. Requires the Pillow module to be installed.")
	parser.add_argument('-c', dest='cleanup', action='store_false', help="By default the script cleans up created files at the end of the process except the generated module. This argument disables cleanup.")
	parser.add_argument('-x', dest='extract', action='store_true', help="Only extracts the image embedded in the provided df2vtt file then exits.")
	parser.add_argument('-t', dest='test_occluder', action='store_true', help="Place wall from 0,0 to the opposite corner of the tile for testing wall generator")
	parser.add_argument('-i', dest='ignore_lights', action='store_true', help="By default lights are processed and included. This causes lights to be excluded in the module.")
	parser.add_argument('-l', dest='log_to_file', action='store_true', help="Log output to file as well as the console.")
	parser.add_argument('-T', dest='test_image', action='store_true', help="Generates preview image with walls and lights (if enabled) marked in colors for testing & validation.")
	parser.add_argument('-N', dest='test_image_textless', action='store_true', help="Same as -T but with no text drawn on the image. This overrides -T.")
	parser.add_argument("-f", dest='grid_size_feet', type=int, default=5, help="Sets the grid size in feet. Used for light ranges.")
	parser.add_argument("-o", dest='ignore_occluders', action='store_true', help="Ignores occluders (walls & doors) when generating module.")
	parser.add_argument("-w", dest='portal_intersect_fix_enabled', action='store_false', help="Disables the fix for walls intersecting portals when they are concealed")
	return parser

query_input = input

def do_args(arg_list):
	global log_level, log_file
	arg_parser = get_argparse()
	args = arg_parser.parse_args(arg_list)

	vprint("Application starting", 'init', args.log_to_file)
	vprint(name + " " + version, 'init', args.log_to_file)

	if args.log_level is not None:
		log_level = args.log_level

	options = {
		"log_level": args.log_level,
		"log_to_file": args.log_to_file,
		"refine_portals": args.refine_portals,
		"door_width": args.door_width,
		"grid_color": args.grid_color,
		"author": args.author,
		"extension": args.extension,
		"do_cleanup": args.cleanup,
		"extract": args.extract,
		"test_occluder": args.test_occluder,
		"ignore_lights": args.ignore_lights,
		"ignore_occluders": args.ignore_occluders,
		"grid_size_real": args.grid_size_feet,
		"test_image": args.test_image,
		"portal_intersect_fix_enabled": args.portal_intersect_fix_enabled,
		"test_image_textless": args.test_image_textless,
	}
	main(args.module_name, args.files, options)

if __name__ == '__main__':
	do_args(sys.argv[1:])
