# Provide a desired module name as the first argument
# Provide any number of Universal VTT json files as individual arguments after that
# Each provided file will be included in the module as a map

import base64
import json
import sys
import re
import os
from sys import argv
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from zipfile import ZipFile

if argv.__len__() == 1:
	print("No module name provided.")
	exit()
elif argv[1] == "workdir":
	print("Workdir: " + os.getcwd())
	exit()

image_id = 1
def generate_image(fn, name, img_ext, grid_size, occluders = []):
	global image_id
	img = Element("id-" + str(image_id).zfill(5))
	SubElement(img, "locked", { "type": "number" }).text = "0"
	SubElement(img, "name", { "type": "string" }).text = name
	image = SubElement(img, "image", { "type": "image" })
	SubElement(image, "grid").text = "on"
	SubElement(image, "gridsize").text = str(grid_size) + "," + str(grid_size)
	SubElement(image, "gridoffset").text = "0,0"
	SubElement(image, "gridsnap").text = "on"
	SubElement(image, "color").text = "#00FFFFFF"
	layers = SubElement(image, "layers")

	layer = SubElement(layers, "layer")
	SubElement(layer, "name").text = name + img_ext
	SubElement(layer, "id").text = "0"
	SubElement(layer, "type").text = "image"
	SubElement(layer, "bitmap").text = fn
	offset_x = 0
	offset_y = 0
	SubElement(layer, "matrix").text = "1,0,0,0,0,1,0,0,0,0,1,0," + str(offset_x) + "," + str(offset_y) + ",0,1"

	occluders = SubElement(layer, "occluders")
	for occ in occluders:
		occluders.append(generate_occluder("points here"))

	image_id += 1
	return img

occluder_id = 1
def generate_occluder(points, toggleable = False, single_sided = False, closed = False):
	global occluder_id
	occluder = Element("occluder")
	SubElement(occluder, "id").text = str(occluder_id).zfill(5)
	occluder_id += 1
	SubElement(occluder, "points").text = "???"
	if toggleable:
		SubElement(occluder, "toggleable")
		if closed:
			SubElement(occluder, "closed")
	if single_sided:
		SubElement(occluder, "single_sided")
	return occluder

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
		# try:
			data = json.loads(json_str)

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

			images.append(generate_image("images/" + filename + ".png", filename, ".png", data["resolution"]["pixels_per_grid"]))
		# except:
		# 	print("Unable to process file '" + arg + "'")
		# 	print("Unexpected error:", sys.exc_info()[0])

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
SubElement(xml_definition_root, "author")
SubElement(xml_definition_root, "ruleset").text = "5E"

with open("definition.xml", 'wb') as f:
	f.write(bytes(xml_version, "utf8") + tostring(xml_definition_root))
to_zip.append("definition.xml")

zip_file = ZipFile(module_id + ".mod", "w")
for f in to_zip:
	zip_file.write(f)
zip_file.close()

print("Finished processing")