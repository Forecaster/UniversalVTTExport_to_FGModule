#!/usr/bin/env

print("Application starting")

from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import df2vtt_parser as parser
import PySimpleGUI as gui
from io import StringIO
import sys
import os
import re

if len(sys.argv) > 1:
	print("Arguments present. Running in command line mode.")
	parser.do_args(sys.argv)
	exit(0)
else:
	print("No arguments present. Running in GUI mode.")

more_options_visible = False

window_query = None
display_str = StringIO()
def query_input(query):
	sys.stdout = sys.__stdout__
	global window_query, display_str
	if not window_query:
		query_counter = 1
		exp = re.compile("A total of (\d*) ")
		match = exp.match(display_str.getvalue())
		if match:
			amt = int(match.group(1))
		else:
			amt = 99
		window_query = gui.Window("Query", [
			[gui.Text("A total of " + str(amt) + " portals were found!")],
			[gui.ProgressBar(amt - 1, orientation='h', size=(20, 20), key='pbar')],
			[gui.Text("")],
			[gui.Text("Choose type for portal #" + str(query_counter), key="str_portal")],
			[gui.DropDown(["Door", "Window", "Toggleable wall", "Illusory wall"], key="ddl_portal")],
			[gui.Button("Previous", key="btn_prev", disabled=True), gui.Button("Next", key="btn_next"), gui.Button("Done", key="btn_done", visible=False)]
		])
		window_query.finalize()
		portals = ["portallist"]
		while True:
			event, values = window_query.read()
			print(event)
			print(values)
			if event == gui.WIN_CLOSED or event == "btn_done":
				try:
					portals[query_counter] = values["ddl_portal"]
				except IndexError:
					portals.insert(query_counter, values["ddl_portal"])
				break
			elif event == "btn_prev":
				try:
					portals[query_counter] = values["ddl_portal"]
				except IndexError:
					portals.insert(query_counter, values["ddl_portal"])
				query_counter = max(1, query_counter - 1)
				window_query["str_portal"].Update("Choose type for portal #" + str(query_counter))
				window_query["pbar"].UpdateBar(query_counter - 1)
			elif event == "btn_next":
				try:
					portals[query_counter] = values["ddl_portal"]
				except IndexError:
					portals.insert(query_counter, values["ddl_portal"])
				query_counter += 1
				window_query["str_portal"].Update("Choose type for portal #" + str(query_counter))
				window_query["pbar"].UpdateBar(query_counter - 1)
			if query_counter == 1:
				window_query["btn_prev"].Update(disabled=True)
			else:
				window_query["btn_prev"].Update(disabled=False)
			if query_counter >= amt:
				window_query["btn_next"].Update(disabled=True)
				window_query["btn_done"].Update(visible=True)
			else:
				window_query["btn_next"].Update(disabled=False)
				window_query["btn_done"].Update(visible=False)
			try:
				window_query["ddl_portal"].Update(portals[query_counter])
			except IndexError:
				window_query["ddl_portal"].Update("")
		window_query.close()
		window_query = None
		display_str = ""
		return ";".join(portals)

pvalue = 1
gui.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
layout = [
	[gui.Text("Module Name - The name displayed in Fantasy Grounds")],
	[gui.InputText("MyModule", focus=True)],
	[gui.Text("Author - The author displayed in Fantasy Grounds")],
	[gui.InputText("DungeonFog")],
	[gui.Text("Choose at least one df2vtt file")],
	[gui.InputText("E:/Core - Development/Web/UniversalVTTExport_to_FGModule/workdir/Ground.df2vtt"), gui.FilesBrowse(file_types=(("Universal VTT", "*.df2vtt"),), initial_folder=os.getcwd())],
	[gui.Button("More options")],
	[gui.Column([
		[gui.Text("Door width"), gui.InputText("10", (10, 10)), gui.Text("pixels deep")],
		[gui.Text("Grid color"), gui.InputText("00000000", (10, 0))],
		[gui.Checkbox("Portal refinement")]], key="more_options", visible=more_options_visible)],
	[gui.Button('Generate')]
]

# Create the Window
window = gui.Window('DungeonFog to Fantasy Grounds Module Generator', layout)

# Event Loop to process "events" and get the "values" of the inputs
while True:
	event, values = window.read()
	if event == gui.WIN_CLOSED: # if user closes window
		if window_query is not None:
			window_query.close()
		break
	elif event == "More options":
		more_options_visible = not more_options_visible
		window["more_options"].update(visible=more_options_visible)
	elif event == "Generate":
		files = []
		try:
			if values[2] == "":
				files = []
			else:
				files = values[2].split(";")
		except AttributeError:
			files = []
		try:
			door_width = int(values[3])
		except ValueError:
			door_width = None

		print("Processing " + str(len(files)) + " file(s)...")

		parser.query_input = query_input
		sys.stdout = display_str

		parser.main(values[0], files=files, refine_portals=values[5], door_width=door_width, grid_color=values[4], author=values[1])
		sys.stdout = sys.__stdout__
		print("Process complete!")

window.close()
