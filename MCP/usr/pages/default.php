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
	public static function Pre() {
		self::$form = new Form();

		$name = new TextBox("Module Name", array("required" => true, "defaultValue" => "MyModule"));
		$author = new TextBox("Module Author", array("placeholder" => "DungeonFog", "description" => "The author the module is credited to. Used for organization within Fantasy Grounds."));
		$files = new FileSelector("df2vtt files", array("acceptedFiles" => array("df2vtt"), "allowMultiple" => true, "minFiles" => 1, "description" => "Max individual file size is 20 MB. Max total file size is 50 MB. A maximum of 20 files can be uploaded at a time."));
		self::$form->AddFields(array($name, $author, $files));
		@session_start();

		if (self::$form->IsSubmitted()) {
			$session_id = session_id();
			$dir_path = __DIR__ . "/../sessions/" . $session_id . "/";
			@mkdir($dir_path, 0777, true);
			$files->MoveUploadedFiles($dir_path);
			$file_list = explode(", ", $files->GetValue());

			$module_name = $name->GetValue();
			$auth = "";
			if (!empty($author->GetValue()))
				$auth = " -a \"" . $author->GetValue() . "\"";
			chdir($dir_path);
			$cmd = escapeshellcmd("python3 " . __DIR__ . "/../../parser.py -v $auth \"$module_name\" \"" . implode("\" \"", $file_list) . "\"");
			self::$cmd_output = shell_exec($cmd);
			if (stristr(self::$cmd_output, "Finished processing ") !== false) {
				self::$path = "usr/sessions/" . $session_id . "/";
				self::$file = array_reverse(explode("\n", self::$cmd_output))[1];
			} else {
				self::$file = false;
			}
		}
	}

	public static function Content1() {
		?>
		<style>
			.changelog {
				background-color: #636363;
				color: white;
				padding: 6px;
				border-radius: 10px;
				margin-top: 10px;
				margin-bottom: 10px;
			}

			.changelog version, .changelog change {
				display: block;
			}

			.changelog version {
				font-weight: bold;
				font-size: 1.2em;
			}

			.changelog change:before {
				content: "• ";
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
			<li>Toggle-able doors & windows</li>
		</ul>
		<?
		$what = new CollapsibleSection("What does this do?", "<p>This generator takes one or more <code>.df2vtt</code> files exported from <a href='https://dungeonfog.com'>DungeonFog</a> and turns them into a module file for Fantasy Grounds.</p><p>This module can then be added to the <code>Modules</code> directory in Fantasy Grounds and loaded within a campaign to access its contents.</p>", "h3");
		$what();
		$how = new CollapsibleSection("How does it do it?", "<p>This page accepts some user input, which includes the <code>.df2vtt</code> files, from the form below and passes it to a parser script that outputs a module file which is then available to download via a link.</p><p>The parser script is written in Python and is made to be usable on its own! See further down!</p>", "h3");
		$how();
		$how_get = new CollapsibleSection("How do I get the script?", "<p>You can download the Python script and run it locally on your computer, though doing so has a couple of prerequisites:<ul><li>You need to have <a href='https://www.python.org/downloads/'>Python</a> installed on your system in some form.</li><li>Some knowledge of command line applications.</li><li>In the absence of the above: A willingness to learn new things.</li></ul></p><p>The methods for getting Python on your specific system (if possible) may vary greatly, so I cannot provide specific instructions other than to go to <a href='https://www.python.org/'>the website</a> and read up on what is available.</p><p>Once you have Python working all you should need to do is <a href='parser.py' download='download'>download the parser script</a> into an empty folder, acquire some <code>.df2vtt</code> files from DungeonFog and place them into the same folder, and navigate to this folder using the command line. (This is generally done using the <code>cd [path]</code> command.) You can call the script from anywhere, but the current folder will be the \\\"working directory\\\" which will make pointing at the <code>.df2vtt</code> files a lot easier, and it's where the module file is placed at the end as well.)</p>", "h3");
		$how_get();
		$how_do = new CollapsibleSection("Using the script", "<p>To use the script you call the parser script from the command line through the Python interpreter.</p><p>To do so type the following into the command line: <code>python parser.py --h</code></p><p>This command tells the Python interpreter to run the script <code>parser.py</code> if it can be found in the current directory. The <code>--h</code> option tells the script to print its usage instructions which should look something like the following:</p><p><code>usage: parser.py [-h] [-a AUTHOR] [-w [WALL_WIDTH]] [-v] [-e EXTENSION]<br/>[-g GRID_COLOR] [--version]<br/>[M] F [F ...]<br/><br/>Converts one or more df2vtt files into a Fantasy Grounds module.<br/><br/>positional arguments:<br/>  M                The name for the output module<br/>  F                One or more paths to df2vtt files to parse into a module<br/><br/>optional arguments:<br/>  -h, --help       show this help message and exit<br/>  -a AUTHOR        Specify the module author (Default: DungeonFog)<br/>  -w [DOOR_WIDTH]  Specify door width (Default: 10)<br/>  -v               Whether detailed debugging output should be provided.<br/>  -e EXTENSION     The desired file name extension for the output module file.<br/>                   (Default: mod)<br/>  -g GRID_COLOR    The grid color. (Default: 000F00AF)<br/>  --version        show program's version number and exit</code></p><p>Once you can see that this is working you can try using the parser in the most basic way:<br/><code>python parser.py \\\"MyModule\\\" \\\"input file 1.df2vtt\\\"</code></p><p>This will take the file <code>input file 1.df2vtt</code>, if it can be found in the working directory, and include it in the output <code>MyModule.mod</code> which, if the parser was successful, should appear in the working directory as well.</p><p>You may also specify multiple input files after the first, all of which will be included in the same module.</p>", "h3");
		$how_do();
		$vid = new CollapsibleSection("Video Tutorial", "<p>I have recorded a video showing the entire process from installing python (on a Windows 10 system) to using the script to get a module to using the new portal refinement mode. It's just under an hour long in its entirety, but it has 8 chapters you can use to navigate the video should you need to.</p><p>You can watch the video on YouTube <a href='https://youtu.be/bAt5vxBlcog' target='_blank'>here</a></p>", "h3");
		$vid();
		$issues = new CollapsibleSection("Notes & Known issues", "<h4>Notes:</h4><ul><li>In this web interface the webserver is limited to receiving a total amount of 50 MB, a maximum of 20 files at once, and each individual file cannot exceed 20 MB. The parser script itself have no such limits.</li><li>Using the web-based parser requires uploading the map files to Forecasters server and downloading the resulting files from it. While these files are not publicly accessible in any way no guarantees are made regarding their security. If you wish for guaranteed security see the sections <code>\\\"How do I get the script?\\\"</code> and <code>\\\"Using the script\\\"</code> on how to generate modules on your own computer.</li><li>If you are generating an updated version of a module you have loaded into Fantasy Grounds previously, make sure you use the same name, or any changes or current token positions within a campaign will be lost.</li></ul><h4>Known issues:</h4><ul><li>Due to limited data within the df2vtt format all windows are treated as doors. Once the file includes tags to distinguish them this will be fixed.</li><li>Curved walls have a rather small amount of points within the exported file which results in noticeable gaps between the LOS wall and the actual wall.</li></ul>", "h3");
		$issues();
		$feedback = new CollapsibleSection("Feedback", "<p>I stated this above, but I'm summarizing it just in case someone misses it (with a nice clear title too):</p><p><b>Any feedback, bug report, or feature request can be delivered in the following ways:</b></p><ul><li>Creating an issue on <a href='https://github.com/Forecaster/UniversalVTTExport_to_FGModule/issues/new/choose'>GitHub</a> (requires a GitHub account)</li><li>Reaching out to Forecaster on the <a href='https://dungeonfog.com/discord'>DungeonFog Discord Server</a> (Requires a Discord account)</li><li>Emailing forecaster at <a href='mailto:df2uvtt@towerofawesome.org'>feedback@towerofawesome.org</a></li></ul>", "h3");
		$feedback();
		?>
		<h3 style="margin-top: 30px;">Generate Module</h3>
		<?

		if (!isset(self::$file))
			echo self::$form->BuildForm();
		elseif (self::$file === false) {
			?>
			<p>Unable to generate module! <a href=".">Try again!</a></p>
			<p>If the issue persist please report this! Check the parser output below and include it in the report!</p>
			<h3>Parser output:</h3>
			<code>
				<?= nl2br(self::$cmd_output) ?>
			</code>
			<?
		} else {
			?>
			<p>Success: <a href='<?= self::$path . self::$file ?>'>Download</a></p>
			<p>This download will remain available for at least an hour, <span class="txt_error">unless you create a module with the same name</span>, in which case the previous module will be overwritten.</p>
			<p><a href=".">Generate another module</a>

			<h3>Parser output:</h3>
				<code>
					<?= nl2br(self::$cmd_output) ?>
				</code>
			<?
		}
		?>
		<br/>
		<p>The following changelog is for the parser script <code>parser.py</code>:</p>
		<div class="changelog">
			<version>v1.1</version>
			<change>[FIX] All doors are walls bug</change>
			<change>[FIX] Missing line in doors</change>
			<change>[FEATURE] Add -p (portal refine) mode to script (not available in web version)</change>
			<version>v1.0</version>
			<change>Initial release</change>
		</div>
		<?
		echo require_once __DIR__ . "/stats.php";
	}
}