#!/usr/bin/env

from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import df2vtt_parser as parser
import PySimpleGUI as gui
from io import StringIO
import sys
import os
import re
import webbrowser

parser.vprint("Application starting", 'init')
parser.vprint(parser.name + " " + parser.version, 'init')

if len(sys.argv) > 1:
	parser.vprint("Arguments present. Running in command line mode. (Run without arguments to run in GUI mode.)", 'init')
	parser.do_args(sys.argv[1:])
	sys.exit(0)
else:
	parser.vprint("No arguments present. Running in GUI mode.", 'init')

more_options_visible = False

window_query: gui.Window = None
def query_input(query):
	global window_query
	if not window_query:
		query_counter = 1
		amt = parser.portal_count_output
		window_query = gui.Window("Query", [
			[gui.Text("A total of " + str(amt) + " portals were found!")],
			[gui.ProgressBar(amt - 1, orientation='h', size=(20, 20), key='pbar')],
			[gui.Text("Open the image generated in the application directory that ends with '_portals.png'.")],
			[gui.Text("Each portal has been assigned a number placed next to each in the image.")],
			[gui.Text("Assign each portal a type below.")],
			[gui.Text("")],
			[gui.Text("Choose type for portal #" + str(query_counter), key="str_portal", size=(40,1))],
			[gui.DropDown(["door", "window", "passage", "toggleable_wall", "illusory_wall"], key="ddl_portal")],
			[gui.Button("Previous", key="btn_prev", disabled=True), gui.Button("Next", key="btn_next"), gui.Button("Done", key="btn_done", visible=False)],
			[gui.Text("")],
			[gui.Text("Types:")],
			[gui.Text("Door - Blocks path & LOS when closed")],
			[gui.Text("Window - Blocks path when closed, never blocks LOS")],
			[gui.Text("Passage - Leaves gap in wall")],
			[gui.Text("Toggleable wall - Like a door, but flush with the wall")],
			[gui.Text("Illusory wall - Blocks LOS, never blocks path, cannot be toggled")]
		], enable_close_attempted_event=True)
		window_query.finalize()
		portals = ["portallist"]
		while True:
			event, values = window_query.read()
			if event == gui.WINDOW_CLOSED or event == "btn_done":
				break
			elif event == gui.WINDOW_CLOSE_ATTEMPTED_EVENT:
				if gui.popup_yes_no('Closing this window will proceed with the processing and assume any unassigned portals are doors.') == 'Yes':
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
		parser.vprint("Query done! (" + event + ")", 'debug')
		try:
			portals[query_counter] = values["ddl_portal"]
		except IndexError:
			portals.insert(query_counter, values["ddl_portal"])
		window_query.close()
		window_query = None
		return ";".join(portals)


default_module = "MyModule"
default_author = "DungeonFog"
default_path = ""
default_portal_width = "10"
default_grid_color = "00000000"
default_portal_refinement = False
default_disable_cleanup = False
default_ignore_lights = False
default_disable_portal_fix = False

pvalue = 1
gui.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
layout = [
	[gui.Text("Module Name - The name displayed in Fantasy Grounds")],
	[gui.InputText(default_module, key="module_name", focus=True)],
	[gui.Text("Author - The author displayed in Fantasy Grounds")],
	[gui.InputText(default_author, key="author_name")],
	[gui.Text("Choose at least one df2vtt file. Multiple paths are separated with ; (Semicolon).")],
	[gui.InputText(default_path, key="files"), gui.FilesBrowse(file_types=(("Universal VTT", "*.df2vtt"),), initial_folder=os.getcwd())],
	[gui.Button("More options")],
	[gui.Column([
		[gui.Text("Portal width", tooltip="Defines the thickness of portals (doors, windows, etc)."), gui.InputText(default_portal_width, (10, 10), key="portal_width"), gui.Text("pixels deep")],
		[gui.Text("Grid color", tooltip="A hex color code where the first number is alpha. Default is 0% opacity black grid."), gui.InputText(default_grid_color, (10, 0), key="grid_color")],
		[gui.Checkbox("Portal refinement", default=default_portal_refinement, tooltip="Enabled portal refinement step. By default all portals (doors, windows, etc) are defined as doors.", key="portal_refinement")],
		[gui.Checkbox("Disable cleanup", default=default_disable_cleanup, tooltip="Disabled cleanup of generated files after assembling module file.", key="disable_cleanup")],
		[gui.Checkbox("Ignore lights", default=default_ignore_lights, tooltip="By default lights are processed and included. This causes lights to be excluded in the module.", key="ignore_lights")],
		[gui.Checkbox("Disable portal fix", default=default_disable_portal_fix, tooltip="Disabled the fix for concealed doors not removing walls.", key="disable_portal_fix")]
	], key="more_options", visible=more_options_visible)],
	[gui.Button('Generate')],
	[gui.Text("About", key="link_about", enable_events=True)],
]

layout_about = [
	[gui.Text("This program was made by Forecaster and generates Fantasy")],
	[gui.Text("Grounds Unity modules from maps exported from DungeonFog")],
	[gui.Text("using the Universal VTT format.")],
	[gui.Text("")],
	[gui.Text("Written in Python and packaged into an executable using PyInstaller.")],
	[gui.Text("")],
	[gui.Text("Links:")],
	[gui.Text("Website", enable_events=True, key="link_website")],
	[gui.Text("GitHub", enable_events=True, key="link_github")],
	[gui.Text("DungeonFog", enable_events=True, key="link_dungeonfog")],
	[gui.Text("FantasyGrounds", enable_events=True, key="link_fantasygrounds")],
]

# Create the Window
window = gui.Window(parser.name + " " + parser.version, layout, finalize=True)
window["link_about"].set_cursor("hand2")

win_about = None

# Event Loop to process "events" and get the "values" of the inputs
while True:
	event, values = window.read()
	module_name = default_module
	author_name = default_author
	path = default_path
	portal_width = default_portal_width
	grid_color = default_grid_color
	portal_refinement = default_portal_refinement
	disable_cleanup = default_disable_cleanup
	ignore_lights = default_ignore_lights
	try:
		module_name = values["module_name"]
	except:
		pass
	try:
		author_name = values["author_name"]
	except:
		pass
	try:
		path = values["files"]
	except:
		pass
	try:
		portal_width = values["portal_width"]
	except:
		pass
	try:
		grid_color = values["grid_color"]
	except:
		pass
	try:
		portal_refinement = values["portal_refinement"]
	except:
		pass
	try:
		disable_cleanup = values["disable_cleanup"]
	except:
		pass
	try:
		ignore_lights = values["ignore_lights"]
	except:
		pass

	if event == gui.WIN_CLOSED: # if user closes window
		break
	elif event == "More options":
		more_options_visible = not more_options_visible
		window["more_options"].update(visible=more_options_visible)
	elif event == "Generate":
		print("'" + values['files'] + "'")
		if values['files'] == "":
			gui.popup("No files chosen for processing.\n\nSelect at least one df2vtt file by using the Browse button or by entering paths or filenames manually.", keep_on_top=True)
		else:
			files = []
			try:
				if path == "":
					files = []
				else:
					files = path.split(";")
			except AttributeError:
				files = []

			parser.vprint("Processing " + str(len(files)) + " file(s)...", 'info')

			parser.query_input = query_input
			parser.log_file = True

			parser.vprint("This is a debug message", 'debug')

			options = {
				"log_level": "debug",
				"log_to_file": True,
				"refine_portals": portal_refinement,
				"door_width": portal_width,
				"grid_color": grid_color,
				"author": author_name,
				"do_cleanup": not disable_cleanup,
				"ignore_lights": ignore_lights,
				"portal_refine_output_override": True,
			}
			parser.main(module_name, files=files, options=options)
			parser.vprint("Process complete!", 'debug')
	elif event == "link_about":
		parser.vprint("Open about window", 'debug')
		win_about = gui.Window("About", layout_about, finalize=True)
		win_about["link_website"].set_cursor("hand2")
		win_about["link_github"].set_cursor("hand2")
		win_about["link_dungeonfog"].set_cursor("hand2")
		win_about["link_fantasygrounds"].set_cursor("hand2")
	else:
		parser.vprint("Unknown event: '" + event + "'", 'error')

	if win_about is not None:
		event, values = win_about.read()
		if event == "link_website":
			webbrowser.open("https://towerofawesome.org/df2uvtt")
		elif event == "link_github":
			webbrowser.open("https://github.com/Forecaster/UniversalVTTExport_to_FGModule")
		elif event == "link_dungeonfog":
			webbrowser.open("https://dungeonfog.com")
		elif event == "link_fantasygrounds":
			webbrowser.open("https://fantasygrounds.com")

if window_query is not None:
	window_query.close()
window.close()
