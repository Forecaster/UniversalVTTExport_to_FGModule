# Provide a desired module name as the first argument
# Provide any number of Universal VTT json files as individual arguments after that
# Each provided file will be included in the module as a map

import base64
import json
from sys import argv

used_image_names = []
module_name = argv[1]
counter = 0
for arg in argv:
	json_str = None
	data = None
	if counter > 1:
		print("Export file: " + arg)
		with open(arg) as f:
			json_str = f.read()
		try:
			data = json.loads(json_str)

			imgstring = data['image']

			imgdata = base64.b64decode(imgstring)
			filename = arg
			filename_counter = 0
			while used_image_names.__contains__(filename):
				filename_counter += 1
				filename += "_" + str(filename_counter)
			with open(filename + ".png", 'wb') as f:
				f.write(imgdata)
		except Exception:
			print("Unable to process file '" + arg + "': " + Exception)
	counter += 1
print("Finished processing")