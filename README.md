# UniversalVTTExport_to_FGModule

## What?
This is a parser written in Python that converts UniversalVTT exports from the DungeonFog battle map editor
to Fantasy Grounds modules.

The generated modules are ready to load right into a Fantasy Grounds campaign and support line of sight.

## How?
The generator can be used online on [this page](https://towerofawesome.org/df2uvtt/) with
limited options, or downloaded as an executable and used via the GUI or
commandline, or you can download the individual Python scripts and run
them via the commandline.

* For the latest executable release see [releases](https://github.com/Forecaster/UniversalVTTExport_to_FGModule/releases)
* For the Python scripts the following files are
  required: `df2vtt_parser.py`, `fg_module.py`, and `utilib.py`

## The executable
You can simply double-click the executable to start the application in GUI mode, or start
it from the commandline with no options. Running it with any options will run in no-GUI mode.

## The Python scripts
You run the `df2vtt_parser.py` by calling it through the Python
interpreter: `python df2vtt_parser`. Running with no arguments will print usage
instructions. Running `df2vtt_paser --help` will print a list of all available
options with descriptions as well as the script version. You can also
run `df2vtt_parser --version` to print the current version.

Additionally, you can run the `parser_gui.py` script to launch
the GUI (The other files are still required).

## Feedback
Any bug report, feature request, or other feedback can be delivered in the following ways:

* Creating an issue [here on GitHub](https://github.com/Forecaster/UniversalVTTExport_to_FGModule/issues/new/choose)
* Reaching out to Forecaster on the [DungeonFog Discord Server](https://dungeonfog.com/discord) (Requires a Discord account)
* Emailing forecaster at [feedback@towerofawesome.org](mailto:feedback@towerofawesome.org) Put `df2vtt` in the subject please!