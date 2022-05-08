import traceback
from xml.etree.ElementTree import Element, SubElement, tostring

import shapely.geometry
import df2vtt_parser as parser

import utilib

image_id = 1
def generate_image(fn, name, img_ext, grid_size, grid_color, img_occluders=None, img_offset_x = 0, img_offset_y = 0, img_lights = None):
	if img_occluders is None:
		img_occluders = []
	if img_lights is None:
		img_lights = []
	global image_id
	layer_id = 0
	img = Element("id-" + str(image_id).zfill(5))
	SubElement(img, "uselighting").text = "on"
	SubElement(img, "locked", { "type": "number" }).text = "0"
	SubElement(img, "name", { "type": "string" }).text = name
	image = SubElement(img, "image", { "type": "image" })
	SubElement(image, "grid").text = "on"
	SubElement(image, "gridsize").text = str(grid_size) + "," + str(grid_size)
	SubElement(image, "gridoffset").text = "0,0"
	SubElement(image, "gridsnap").text = "on"
	SubElement(image, "color").text = "#" + grid_color
	layers = SubElement(image, "layers")

	layer = SubElement(layers, "layer")
	SubElement(layer, "name").text = name + img_ext
	SubElement(layer, "id").text = str(layer_id)
	layer_id += 1
	SubElement(layer, "type").text = "image"
	SubElement(layer, "bitmap").text = fn
	SubElement(layer, "matrix").text = "1,0,0,0,0,1,0,0,0,0,1,0," + str(img_offset_x) + "," + str(img_offset_y) + ",0,1"

	if img_lights.__len__() > 0:
		# img_xml_lights_layer = SubElement(layers, "layer")
		# SubElement(img_xml_lights_layer, "name").text = "Lights"
		# SubElement(img_xml_lights_layer, "id").text = str(layer_id)
		# layer_id += 1
		# SubElement(img_xml_lights_layer, "parentid").text = "-3"
		# SubElement(img_xml_lights_layer, "type").text = "image"
		# SubElement(img_xml_lights_layer, "bitmap")
		# img_xml_lights = SubElement(img_xml_lights_layer, "lights")
		img_xml_lights = SubElement(layer, "lights")
		for this_light in img_lights:
			img_xml_lights.append(generate_light(this_light["x"], this_light["y"], color=this_light["color"], range_pixels_bright=this_light["range_pixels"], range_pixels_dim=this_light["range_pixels"]*2, range_tiles_bright=this_light["range_tiles"], range_tiles_dim=this_light["range_tiles"]*2))

	# Intersection scan
	wall_counter = 0
	intersection_counter = 0
	# print("Start intersect scan..")
	for a in range(len(img_occluders)):
		occA = img_occluders[a]
		if occA["type"] == "wall":
			wall_counter += 1
			for b in range(a + 1, len(img_occluders)):
				occB = img_occluders[b]
				if occB["type"] == "wall":
					# print("a" + str(a) + " vs " + "b" + str(b))
					pointsA = occA["points"].split(",")
					pointsB = occB["points"].split(",")
					lineA = ((float(pointsA[0]), float(pointsA[1])), (float(pointsA[2]), float(pointsA[3])))
					lineB = ((float(pointsB[0]), float(pointsB[1])), (float(pointsB[2]), float(pointsB[3])))
					intersect = utilib.intersects(lineA, lineB)
					# print(intersect)
					if intersect:
						# print("a" + str(a), occA)
						# print("b" + str(b), occB)
						inters = utilib.get_intersect_point(lineA, lineB)
						# print(str(inters) + " is close to lineA1", utilib.points_close(lineA[0], inters))
						# print(str(inters) + " is close to lineA2", utilib.points_close(lineA[1], inters))
						# print(str(inters) + " is close to lineB1", utilib.points_close(lineB[0], inters))
						# print(str(inters) + " is close to lineB2", utilib.points_close(lineB[1], inters))
						if utilib.true_intersect_check(lineA, lineB, inters):
							intersection_counter += 1
							try:
								new_occ_a = { "points": str(lineA[0][0]) + "," + str(lineA[0][1]) + "," + str(inters[0]) + "," + str(inters[1]) + "," + str(lineA[1][0]) + "," + str(lineA[1][1]), "type": "wall" }
								new_occ_b = { "points": str(lineB[0][0]) + "," + str(lineB[0][1]) + "," + str(inters[0]) + "," + str(inters[1]) + "," + str(lineB[1][0]) + "," + str(lineB[1][1]), "type": "wall" }
							except Exception:
								print("Error during intersect check!")
								print("lineA: " + str(lineA))
								print("lineB: " + str(lineB))
								print("Inters: " + str(inters))
								print(traceback.format_exc())
								exit()
							# print(new_occ_a)
							# print(new_occ_b)
							img_occluders[a] = new_occ_a
							img_occluders[b] = new_occ_b

	inter_s = "s"
	if intersection_counter == 1:
		inter_s = ""
	utilib.vprint("Intersection scan complete on " + str(wall_counter) + " walls. " + str(intersection_counter) + " intersection" + inter_s + " found.", 'info')

	img_xml_occluders = SubElement(layer, "occluders")
	for occ in img_occluders:
		occluder = generate_simple_occluder(occ["points"], occ["type"])
		if occluder is None:
			utilib.vprint("Type '" + occ["type"] + "' is not a valid simple occluder type.", 'warn')
		else:
			img_xml_occluders.append(occluder)

	image_id += 1
	return img

occluder_id = 0
def generate_occluder(points, override_id = None, toggleable = False, hidden = False, single_sided = False, terrain = False, allow_move = False, closed = True, allow_vision = False, counterclockwise = False, shadow = False, pit = False):
	global occluder_id
	if override_id is None:
		override_id = occluder_id
		occluder_id += 1
	occluder = Element("occluder")
	SubElement(occluder, "id").text = str(override_id)
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
	if hidden:
		SubElement(occluder, "hidden")
	if terrain:
		SubElement(occluder, "terrain")
	if shadow:
		SubElement(occluder, "shadow")
	if pit:
		SubElement(occluder, "pit")
	if allow_move:
		SubElement(occluder, "allow_move")
	return occluder

def generate_simple_occluder(points, occluder_type = None, override_id = None):
	if occluder_type is None:
		occluder_type = "wall"
	occluder_type = occluder_type.lower()
	if occluder_type == "wall":
		return generate_occluder(points, override_id = override_id, closed=True)
	elif occluder_type == "terrain":
		return generate_occluder(points, override_id = override_id, toggleable=True, hidden=True, single_sided=True, terrain=True, allow_move=True, closed=True, counterclockwise=True)
	elif occluder_type == "door":
		return generate_occluder(points, override_id = override_id, toggleable=True, single_sided=True, closed=True, counterclockwise=True)
	elif occluder_type == "toggleable_wall":
		return generate_occluder(points, override_id = override_id, toggleable=True, hidden=True, closed=False)
	elif occluder_type == "window":
		return generate_occluder(points, override_id = override_id, toggleable=True, allow_vision=True, closed=True)
	elif occluder_type == "illusory_wall":
		return generate_occluder(points, override_id = override_id, allow_move=True, closed=True)
	elif occluder_type == "pit":
		return generate_occluder(points, override_id = override_id, toggleable=True, hidden=True, single_sided=True, pit=True, closed=True, counterclockwise=True)
	elif occluder_type == "shadow_caster":
		return generate_occluder(points, override_id = override_id, hidden=True, single_sided=True, allow_move=True, closed=True, counterclockwise=True, shadow=True)
	return None

light_id = 0
def generate_light(light_position_x, light_position_y, range_pixels_bright, range_pixels_dim, range_tiles_bright, range_tiles_dim, color, on = True, falloff_bright = 0.75, falloff_dim = 0.5):
	global light_id
	xml_light = Element("light")
	SubElement(xml_light, "id").text = str(light_id)
	SubElement(xml_light, "position").text = str(light_position_x) + "," + str(light_position_y)
	SubElement(xml_light, "range").text = str(range_tiles_bright) + "," + str(falloff_bright) + "," + str(range_tiles_dim) + "," + str(falloff_dim)
	SubElement(xml_light, "color").text = "#" + color
	# light_los = SubElement(xml_light, "los")
	# points = []
	# for p in generate_light_radius_points(light_position_x, light_position_y, range_pixels_bright):
	# 	points.append(str(p[0]))
	# 	points.append(str(p[1]))
	# SubElement(light_los, "points").text = ",".join(points)
	if on:
		SubElement(xml_light, "on")

	light_id += 1
	return xml_light

def generate_light_radius_points(light_pos_x, light_pos_y, light_range):
	origin = shapely.geometry.Point(light_pos_x, light_pos_y)
	circle = origin.buffer(light_range)
	return circle.exterior.coords

def generate_ambient(color, shadow_color="#FF668096", direction=0.7826707, shadow_length=0.5458138, mask=False):
	xml_ambient = Element("ambient")
	SubElement(xml_ambient, "ambientcolor").text = color
	SubElement(xml_ambient, "shadowcolor").text = shadow_color
	SubElement(xml_ambient, "lightdir").text = str(direction)
	SubElement(xml_ambient, "shadowlength").text = str(shadow_length)
	if mask:
		SubElement(xml_ambient, "useambientmask")
		ambient_mask = SubElement(xml_ambient, "ambientmask")
		for points in mask:
			SubElement(ambient_mask, "points").text = points
	return xml_ambient
