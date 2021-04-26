<?
require_once __DIR__ . "/../../internal/BaseModule.php";
require_once __DIR__ . "/../../internal/Capabilities.php";
Capabilities::load(array(Capabilities::$FORM, Capabilities::$KRUMO));

class ModuleDefault extends BaseModule {
	public static function GetTitle($page_title = "") {
		return parent::GetTitle("Default Page");
	}

	private static $form;
	private static $path;
	private static $file;
	public static function Pre() {
		self::$form = new Form();

		$name = new TextBox("Module Name", array("required" => true, "defaultValue" => "MyModule"));
		$author = new TextBox("Module Author", array("placeholder" => "DungeonFog", "description" => "The author the module is credited to. Used for organization within Fantasy Grounds."));
		$files = new FileSelector("df2vtt files", array("acceptedFiles" => array("df2vtt"), "allowMultiple" => true, "minFiles" => 1));
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
			$cmd_output = shell_exec($cmd);
			if (stristr($cmd_output, "Finished processing ") !== false) {
				self::$path = "usr/sessions/" . $session_id . "/";
				self::$file = array_reverse(explode("\n", $cmd_output))[1];
			} else {
				self::$file = false;
			}
		}
	}

	public static function Content1() {
		?>
		<p><h2>Hello! Welcome to the Fantasy Grounds module generator for DungeonFog</h2></p>
		<p>This is a converter for turning one or more <code>.df2vtt</code> files (in the Universal VTT format) into a Fantasy Grounds module.</p>
		<p>To do this simply sacrifice a billionaire at your nearest sacrificing location.</p>
		<p>You may also wish to do this locally on your own machine. This is possible by downloading the <a href="parser.py">Python script</a> used to generate the modules and running it locally.</p>
		<p>Doing this requires that your system can run Python scripts and familiarity with the command line, or a desire to learn.</p>
		<p>This page and the module generating script was created by Forecaster. If you need help you can find him on the <a href="https://dungeonfog.com/discord">DungeonFog Discord</a> server.</p>
		<p>There is also a <a href="https://github.com/Forecaster/UniversalVTTExport_to_FGModule">GitHub repository</a> where you can find the code for this page as well as the Python script. There you can also report issues related to this project.</p>
		<p>Note: The maximum filesize is 20 MB, and the total max size is 50 MB. If you want to handle files larger than this or with a larger total size you need to download the Python script and run it locally.</p>

		<h3>Generate Module</h3>
		<?

		if (!isset(self::$file))
			echo self::$form->BuildForm();
		elseif (self::$file === false) {
			?>
			<div>Unable to generate module! <a href=".">Try again!</a> If the issue persist please report this!</div>
			<?
		} else {
			?>
			<p>Success: <a href='<?= self::$path . self::$file ?>'>Download</a></p>
			<p>This download will remain available for at least an hour, <span class="txt_error">unless you create a module with the same name</span>, in which case the previous module will be overwritten.</p>
			<p><a href=".">Generate another module</a></p>
			<?
		}
	}
}