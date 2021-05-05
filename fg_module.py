
from xml.etree.ElementTree import Element, SubElement, tostring

image_id = 1
def generate_image(fn, name, img_ext, grid_size, grid_color, img_occluders=None, img_offset_x = 0, img_offset_y = 0, img_lights = None):
	if img_occluders is None:
		img_occluders = []
	if img_lights is None:
		img_lights = []
	global image_id
	img = Element("id-" + str(image_id).zfill(5))
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
	SubElement(layer, "id").text = "0"
	SubElement(layer, "type").text = "image"
	SubElement(layer, "bitmap").text = fn
	SubElement(layer, "matrix").text = "1,0,0,0,0,1,0,0,0,0,1,0," + str(img_offset_x) + "," + str(img_offset_y) + ",0,1"

	img_xml_occluders = SubElement(layer, "occluders")
	for occ in img_occluders:
		img_xml_occluders.append(generate_simple_occluder(occ["points"], occ["type"]))

	if img_lights.__len__() > 0:
		img_xml_lights_layer = SubElement(layers, "layer")
		SubElement(img_xml_lights_layer, "name").text = "Lights"
		SubElement(img_xml_lights_layer, "id").text = "1"
		SubElement(img_xml_lights_layer, "parentid").text = "-3"
		SubElement(img_xml_lights_layer, "type").text = "image"
		SubElement(img_xml_lights_layer, "bitmap")
		img_xml_lights = SubElement(img_xml_lights_layer, "lights")
		for this_light in img_lights:
			img_xml_lights.append(generate_light(this_light["x"], this_light["y"], this_light["range"], this_light["range"]/2, this_light["color"]))

	image_id += 1
	return img

occluder_id = 0
def generate_occluder(points, toggleable = False, hidden = False, single_sided = False, terrain = False, allow_move = False, closed = True, allow_vision = False, counterclockwise = False, shadow = False, pit = False):
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

def generate_simple_occluder(points, occluder_type = None):
	if occluder_type is None:
		occluder_type = "wall"
	if occluder_type == "wall":
		return generate_occluder(points, closed=True)
	elif occluder_type == "terrain":
		return generate_occluder(points, toggleable=True, hidden=True, single_sided=True, terrain=True, allow_move=True, closed=True, counterclockwise=True)
	elif occluder_type == "door":
		return generate_occluder(points, toggleable=True, single_sided=True, closed=True, counterclockwise=True)
	elif occluder_type == "toggleable_wall":
		return generate_occluder(points, toggleable=True, hidden=True, closed=True)
	elif occluder_type == "window":
		return generate_occluder(points, toggleable=True, allow_vision=True, closed=True)
	elif occluder_type == "illusory_wall":
		return generate_occluder(points, allow_move=True, closed=True)
	elif occluder_type == "pit":
		return generate_occluder(points, toggleable=True, hidden=True, single_sided=True, pit=True, closed=True, counterclockwise=True)
	elif occluder_type == "shadow_caster":
		return generate_occluder(points, hidden=True, single_sided=True, allow_move=True, closed=True, counterclockwise=True, shadow=True)
	return None

light_id = 0
def generate_light(light_position_x, light_position_y, bright_range, dim_range, color, on = True):
	global light_id
	xml_light = Element("light")
	SubElement(xml_light, "id").text = str(light_id)
	SubElement(xml_light, "position").text = str(light_position_x) + "," + str(light_position_y)
	SubElement(xml_light, "range").text = str(dim_range) + ",0.75," + str(bright_range) + ",0.5"
	SubElement(xml_light, "color").text = color
	light_los = SubElement(xml_light, "los")
	SubElement(light_los, "points").text = "306.7,-525,112.1,-525,105.2,-524.4,4.2,-497.3,-90.6,-453.1,-176.3,-393.1,-250.3,-319.2,-310.3,-233.5,-354.5,-138.7,-381.5,-37.7,-385.4,7.2,-104.4,35.1,-104.4,157.6,-364.8,233.2,-354.5,271.7,-310.3,366.5,-298.3,383.6,-104.4,262.5,-104.4,385.2,-210.1,492.4,-177.4,525,596.1,525,669,452.2,729,366.5,773.2,271.7,800.2,170.7,809.4,66.5,800.2,-37.7,773.2,-138.7,729,-233.5,669,-319.2,595,-393.1,509.4,-453.1,414.6,-497.3,313.6,-524.4"
	if on:
		SubElement(xml_light, "on")

	light_id += 1
	return xml_light
