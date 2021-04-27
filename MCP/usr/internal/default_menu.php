<?
Capabilities::load(array(Capabilities::$MENU, Capabilities::$CONFIG));

$menu_root = (defined('SITE_ROOT_URL') ? "/" . SITE_ROOT_URL : "");

$menu = new MenuStructure();

$menu->AddItem(new MenuLink("Home", $menu_root, "Reload this page"));
$menu->AddItem(new MenuLink("GitHub", "https://github.com/Forecaster/UniversalVTTExport_to_FGModule", "The GitHub repository for this project"));
$menu->AddItem(new MenuLink("DungeonFog", "https://dungeonfog.com", "DungeonFog Website"));
$menu->AddItem(new MenuLink("DF Discord", "https://dungeonfog.com/discord", "DungeonFog Discord Server"));

return $menu;