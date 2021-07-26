<?
require_once __DIR__ . "/../../internal/BaseModule.php";
Capabilities::load(array(Capabilities::$FORM, Capabilities::$KRUMO, Capabilities::$COLLAPSIBLE_SECTION, Capabilities::$BOOTSTRAP_ICONS));

class ModuleDefault extends BaseModule {
	public static function GetTitle($page_title = "") {
		return parent::GetTitle();
	}

	private static $form;
	private static $path;
	private static $file;
	private static $cmd_output;
	private static $script_error = false;
	public static function Pre() {
		self::$form = new Form();

		$name = new TextBox("Module Name", array("required" => true, "defaultValue" => "MyModule"));
		$author = new TextBox("Module Author", array("placeholder" => "DungeonFog", "description" => "The author the module is credited to. Used for organization within Fantasy Grounds."));
		$files = new FileSelector("df2vtt files", array("acceptedFiles" => array("df2vtt"), "allowMultiple" => true, "minFiles" => 1, "description" => "Max individual file size is 20 MB. Max total file size is 50 MB. A maximum of 20 files can be uploaded at a time."));
		$ignore_lights = new CheckBox("Ignore lights");
		$ignore_walls_and_doors = new CheckBox("Ignore walls & doors");
		self::$form->AddFields(array($name, $author, $files, $ignore_lights, $ignore_walls_and_doors));

		if (self::$form->IsSubmitted()) {
			$session_id = uniqid("", true);
			$dir_path = __DIR__ . "/../sessions/" . $session_id . "/";
			@mkdir($dir_path, 0777, true);
			$files->MoveUploadedFiles($dir_path);
			$file_list = explode(", ", $files->GetValue());

			$module_name = $name->GetValue();
			$auth = "";
			if (!empty($author->GetValue()))
				$auth = " -a \"" . $author->GetValue() . "\"";
			chdir($dir_path);
			$options = "-v";
			if ($ignore_lights->GetValue() == true)
				$options .= "i";
			if ($ignore_walls_and_doors->GetValue() == true)
				$options .= "o";
			$cmd = escapeshellcmd("python3 " . __DIR__ . "/../generator_scripts/df2vtt_parser.py $options $auth \"$module_name\" \"" . implode("\" \"", $file_list) . "\"") . " 2>&1";
			try {
				@$final_line = exec($cmd, self::$cmd_output, $result_code);
			} catch (Exception $e) {
				self::$cmd_output = array($e->getMessage());
			}
			if (count(self::$cmd_output) == 0)
				self::$cmd_output = array("No output from parser... If this issue persists please notify us!");
			if ($result_code != 0) {
				self::$script_error = true;
			}
			self::$cmd_output = implode("\n", self::$cmd_output) . "\n\nProgram exited with code " . $result_code;
			self::$cmd_output = preg_replace('/".*\/generator_scripts\//m', "\"<truncated_path>/generator_scripts/", self::$cmd_output);
			if ($result_code == 0) {
				self::$path = "usr/sessions/" . $session_id . "/";
				self::$file = $final_line;
			} else {
				self::$file = false;
			}
		}
	}

	public static function Content1() {
		?>
		<style>
			.error {
				color: red;
				font-weight: bold;
				font-size: 1.2em;
				background-color: black;
				padding: 5px 40px 5px 40px;
				display: inline-block;
				border-radius: 15px;
			}

			.changelog {
				background-color: #636363;
				color: white;
				padding: 6px;
				border-radius: 10px;
				margin-top: 10px;
				margin-bottom: 10px;
			}

			.changelog version, .changelog change, .changelog date, .changelog fix, .changelog feature, .changelog note, .changelog release, .changelog critical {
				display: block;
			}

			.changelog date {
				font-weight: bold;
				font-size: 1.2em;
			}

			.changelog release:before {
				content: '• [RELEASE] ';
				font-weight: bold;
			}

			.changelog release {
				color : #63ff63;
			}

			.changelog version:before {
				content: '• [VERSION] ';
			}

			.changelog change:before {
				content: '• [CHANGE] ';
			}

			.changelog fix:before {
				content: '• [FIX] ';
			}

			.changelog feature:before {
				content: '• [FEATURE] ';
			}

			.changelog critical:before {
				content: '• [CRITICAL] ';
			}

			.changelog critical {
				color: #ffdf6d;
			}

			.changelog note:before {
				content: '• ';
			}

			.divider {
				margin-top: 40px;
				border-bottom: 1px solid gray;
				margin-bottom:40px;
			}
		</style>
		<p><h2>Hello! Welcome to the Fantasy Grounds module generator for DungeonFog</h2></p>
		<p>This page and the generator itself were coded in their entirety by Forecaster, for the benefit of the venn diagram overlap between DungeonFog users and Fantasy Grounds users (such as myself).</p>
		<p>You can get started right away by using the form below, or read on for more information!</p>
		<p>If, after reading the sections below, you need additional help, or want to report an issue, you can find Forecaster on the <a href="https://dungeonfog.com/discord">DungeonFog discord</a>. You can also report issues and submit feature requests on this projects <a href="https://github.com/Forecaster/UniversalVTTExport_to_FGModule">GitHub repository</a> (requires a GitHub account).</p>
		<p>On the GitHub page you can also find all the code associated with this project, which includes the parser and this page.</p>
		<h4>Features:</h4>
		<ul>
			<li>Import of map image</li>
			<li>Wall definitions for Line of Sight</li>
			<li>Doors, windows, toggleable walls, & illusory walls</li>
			<li>Lighting</li>
		</ul>
		<?
		$what = new CollapsibleSection("What does this do?", array(
			"<p>This generator takes one or more <code>.df2vtt</code> files exported from <a href='https://dungeonfog.com'>DungeonFog</a> and turns them into a module file for Fantasy Grounds. (One module can contain multiple maps)</p>",
			"<p>This module can then be added to the <code>Modules</code> directory in Fantasy Grounds and loaded within a campaign to access its contents.</p>"), "h3");
		$how_get = new CollapsibleSection("How do I use the generator?", array(
			"<p><b>You have three choices for using the generator, and they are as follows:</b>",
			"<ol><li>Use the limited online generator on this page. Easy.</li>",
			"<li><a href='https://github.com/Forecaster/UniversalVTTExport_to_FGModule/releases'>Download the executable</a> and run the generator locally. Intermediate.</li>",
			"<li><a href='https://github.com/Forecaster/UniversalVTTExport_to_FGModule'>Download the Python scripts</a> and run the generator via the commandline. Expert.</li></ol>",
			"<p>Each of these have their own advantages and drawbacks. See the following sections for more information about each.</p>"), "h3");
		$web_generator = new CollapsibleSection("Online Generator", array(
			"<p>The web generator is easy and quick to use, and requires no setup, but it does require uploading the <code>.df2vtt</code> files and then downloading the resulting module. This of course requires an internet connection.</p>",
			"<p>There are also some restrictions on file sizes:</p>",
			"<ul><li>A maximum of 20 files can be uploaded to create a single module.</li>",
			"<li>Each file can be a maximum of 20 MB.</li>",
			"<li>The maximum total size of all the files combined is 50 MB.</li></ul>",
			"<p>There are also no settings available for the online generator at the moment.</p>"), "h3");
		$exe_generator = new CollapsibleSection("Executable", array(
			"<p>You can <a href='https://github.com/Forecaster/UniversalVTTExport_to_FGModule/releases'>download the generator as an executable</a> which includes everything required to run it.</p>",
			"<p>With this you can generate modules locally on your system without an internet connection or having to send the map files anywhere. You also get access to more options, such as the portal refinement system, and more.</p>",
			"<p>The executable can also be run from the commandline without the GUI if required.</p>"
		), "h3");
		$script_generator = new CollapsibleSection("Python Scripts", array(
			"<p>Advanced users may wish to <a href='https://github.com/Forecaster/UniversalVTTExport_to_FGModule'>download the raw Python scripts</a> which can be through the Python interpreter.</p>",
			"<p>This requires the correct libraries to be installed in the Python environment.</p>",
			"<p>I'm not going to provide instructions on how to do this. The generator will complain if you try to use a feature without the required libraries installed.</p>"
		), "h3");
//		$how_do = new CollapsibleSection("Using the script", "<p>To use the script you call the parser script from the command line through the Python interpreter.</p><p>To do so type the following into the command line: <code>python parser.py --h</code></p><p>This command tells the Python interpreter to run the script <code>parser.py</code> if it can be found in the current directory. The <code>--h</code> option tells the script to print its usage instructions which should look something like the following:</p><p><code>usage: parser.py [-h] [-a AUTHOR] [-w [WALL_WIDTH]] [-v] [-e EXTENSION]<br/>[-g GRID_COLOR] [--version]<br/>[M] F [F ...]<br/><br/>Converts one or more df2vtt files into a Fantasy Grounds module.<br/><br/>positional arguments:<br/>  M                The name for the output module<br/>  F                One or more paths to df2vtt files to parse into a module<br/><br/>optional arguments:<br/>  -h, --help       show this help message and exit<br/>  -a AUTHOR        Specify the module author (Default: DungeonFog)<br/>  -w [DOOR_WIDTH]  Specify door width (Default: 10)<br/>  -v               Whether detailed debugging output should be provided.<br/>  -e EXTENSION     The desired file name extension for the output module file.<br/>                   (Default: mod)<br/>  -g GRID_COLOR    The grid color. (Default: 000F00AF)<br/>  --version        show program's version number and exit</code></p><p>Once you can see that this is working you can try using the parser in the most basic way:<br/><code>python parser.py \\\"MyModule\\\" \\\"input file 1.df2vtt\\\"</code></p><p>This will take the file <code>input file 1.df2vtt</code>, if it can be found in the working directory, and include it in the output <code>MyModule.mod</code> which, if the parser was successful, should appear in the working directory as well.</p><p>You may also specify multiple input files after the first, all of which will be included in the same module.</p>", "h3");
//		$how_do();
//		$vid = new CollapsibleSection("Video Tutorial", "<p>I have recorded a video showing the entire process from installing python (on a Windows 10 system) to using the script to get a module to using the new portal refinement mode. It's just under an hour long in its entirety, but it has 8 chapters you can use to navigate the video should you need to.</p><p>You can watch the video on YouTube <a href='https://youtu.be/bAt5vxBlcog' target='_blank'>here</a></p>", "h3");
		$issues = new CollapsibleSection("Notes & Known issues", array("<h4>Notes:</h4>",
			"<ul><li>Using the web-based parser requires uploading the map files to Forecasters server and downloading the resulting files from it. While these files are not publicly accessible in any way, no guarantees are made regarding their security. If you wish for guaranteed security you must run the generator locally. See the other sections for instructions on how to do this.</li>",
			"<li>If you are generating an updated version of a module you have loaded into Fantasy Grounds previously, make sure you use the same name for the module and any maps within, or any changes or current token positions within a campaign will be lost.</li>",
			"</ul>",
			"<h4>Known issues:</h4>",
			"<ul><li>Due to limited data within the df2vtt format all windows are treated as doors by default. To specify which portals are windows, toggleable walls, etc, use the portal refinement mode. Once portals are tagged in the export these will be used to define defaults (though these will not cover all types available in Fantasy Grounds).</li>",
			"</ul>"), "h3");
		$feedback = new CollapsibleSection("Feedback", array("<p>I stated this above, but I'm summarizing it just in case someone misses it (with a nice clear title too):</p>",
			"<p><b>Any bug report, feature request, or other feedback can be delivered in the following ways:</b></p>",
			"<ul><li>Creating an issue on <a href='https://github.com/Forecaster/UniversalVTTExport_to_FGModule/issues/new/choose'>GitHub</a> (requires a GitHub account)</li>",
			"<li>Reaching out to Forecaster on the <a href='https://dungeonfog.com/discord'>DungeonFog Discord Server</a> (Requires a Discord account)</li>",
			"<li>Emailing forecaster at <a href='mailto:feedback@towerofawesome.org'>feedback@towerofawesome.org</a>. Put <code>df2vtt</code> in the subject please!§</li></ul>"), "h3");
		?>
		<h3 style="margin-top: 30px;">Generate Module</h3>
		<h6>For the application version of the module generator see the sections below the form. Get more options and features by downloading the application.</h6>
		<?

		if (!isset(self::$file))
			echo self::$form->BuildForm();
		elseif (self::$file === false || self::$script_error) {
			?>
			<p class="error">An error occurred!</p>
			<p>Unable to generate module! <a href=".">Please try again!</a></p>
			<p>If the issue persist please report this via one of the methods under Feedback! Check the parser output below and include it in the report!</p>
			<h3>Parser output:</h3>
			<textarea readonly="readonly" title="Script output" style="resize: vertical; width: 100%; height: 300px;"><?= self::$cmd_output; ?></textarea>
			<?
		} else {
			?>
			<p>Success: <a href='<?= self::$path . self::$file ?>'>Download</a></p>
			<p>This download will remain available for at least an hour, <span class="txt_error">unless you create a module with the same name</span>, in which case the previous module will be overwritten.</p>
			<p><a href=".">Generate another module</a>

			<h3>Parser output:</h3>
				<textarea readonly="readonly" title="Script output" style="resize: vertical; width: 100%; height: 300px;"><?= self::$cmd_output; ?></textarea>
			<?
		}
		?>
		<div class="divider"></div>
		<p>The module name and list of files are passed to the script as normal. The module author field is passed to the script using the <code>-a</code> parameter.</p>
		<p>Additional options passed to the script:</p>
		<ul>
			<li><code>-v</code> Makes the script output mor detailed information about what it's doing</li>
		</ul>
		<div class="divider"></div>
		<?

		$what();
		$how_get();
		$web_generator();
		$exe_generator();
		$script_generator();
//		$vid();
		$issues();
		$feedback();

		?>
		<div class="divider"></div>
		<p>The following changelog is for the module generator in general, including this web page, the application and the Python scripts. Changes, features, or fixes unless specified may apply to all of these.</p>
		<div class="changelog">
			<date>2021-07-20</date>
			<change>Improve layout of web page</change>
			<change>Improve feedback from script when using form</change>
			<fix>Update generator form to work with updated scripts</fix>
			<date>2021-07-18</date>
			<release>v1.2</release>
			<feature>GUI added</feature>
			<feature>Portal refinement mode added</feature>
			<feature>Light support added</feature>
			<date>2021-05-08</date>
			<release>v1.1</release>
			<fix>All doors are walls bug</fix>
			<fix>Missing line in doors</fix>
			<feature>Add -p (portal refine) mode to script (not available in web version)</feature>
			<date>2021-04-26</date>
			<release>v1.0</release>
			<note>Initial release</note>
		</div>
		<?
		echo require_once __DIR__ . "/stats.php";
	}
}