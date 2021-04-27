<?
Capabilities::load(array(Capabilities::$MENU, Capabilities::$CONFIG));

$menu_root = (defined('SITE_ROOT_URL') ? "/" . SITE_ROOT_URL : "");

$menu = new MenuStructure();

$menu->AddItem(new MenuLink("Home", $menu_root));
$menu->AddItem(new MenuLink("GitHub", "https://github.com/Forecaster/UniversalVTTExport_to_FGModule"));
$menu->AddItem(new MenuLink("Discord", "https://dungeonfog.com/discord"));

return $menu;