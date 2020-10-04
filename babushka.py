import lib.utils as utils

import win32gui
import win32process

enemy_path = "./data/enemy/"
drop_path = "./data/drop/"
map_path = "./data/map/"

import cv2

if __name__ == "__main__":
	player = utils.player()
	time = utils.bot_time()
	error_timer = utils.error_timer()

	enemy_sprites = utils.get_sprites(enemy_path, ["spore"])
	drop_sprites = utils.get_sprites(drop_path, ["spore", "other"])

	map = utils.load_map(map_path, "pay_field_01.txt")

	player.add_spell("Improved concentration",
		utils.spell('F1', 240, 1, utils.spell_type.self))
	player.add_spell("Wind walk",
		utils.spell('7', 400, 1.5, utils.spell_type.self))
	player.add_spell("Double strafe",
		utils.spell('2', 0, 0, utils.spell_type.attack))
	player.add_spell("Charge arrow",
		utils.spell('3', 0, 0, utils.spell_type.attack))

	player.autospell("Improved concentration",
		utils.cast_type.every_time, [lambda dist: player.cur_sp > 70])
	player.autospell("Wind walk",
		utils.cast_type.every_time, [lambda dist: player.cur_sp > 100])

	player.autospell("Charge arrow",
		utils.cast_type.battle, [lambda dist: player.cur_sp > 15 and dist < 3])
	player.autospell("Double strafe",
		utils.cast_type.battle, [lambda dist: player.sp_rate() > 0.8,
		lambda dist: player.cur_sp > 12 and player.hp_rate() < 0.2])

	player.add_potion("Strawberry", utils.potion('6', 0))
	player.add_potion("Wing", utils.potion('8', 0))

	player.autopotion("Strawberry", [lambda : player.sp_rate() < 0.3])

	while "main loop":
		foreground_win_name = win32gui.GetWindowText(win32gui.GetForegroundWindow())
		if foreground_win_name == utils.win_name:
			image = utils.get_screen()

			time.update()
			player.update(map, time.frame_time)

			drop = utils.find_sprites(image, drop_sprites, 0.85)
			enemies = utils.find_sprites(image, enemy_sprites, 0.5)

			utils.debug_draw(image, enemies + drop)

			if len(drop) > 0:
				nearer_drop = utils.find_nearer(player, drop)
				utils.click_to_object(player, nearer_drop, 0.35, 2)
				map.idle_time = 0
				error_timer.drop(player, map, time.frame_time)
			elif len(enemies) > 0:
				nearer_enemy = utils.find_nearer(player, enemies)
				if not player.try_spells(nearer_enemy):
					utils.click_to_enemy(player, nearer_enemy, 0.1, 2)
				map.idle_time = 0
				error_timer.enemy(player, map, time.frame_time)
			else :
				map.move(player, time.frame_time, 0.4)
				error_timer.refresh()

		if cv2.waitKey(25) & 0xFF == ord("q"):
			cv2.destroyAllWindows()
			break
