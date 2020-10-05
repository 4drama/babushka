import lib.utils as utils

import win32gui
import win32process

enemy_path = "./data/enemy/"
drop_path = "./data/drop/"
map_path = "./data/map/"

import cv2

def create_player():
	player = utils.player()

	player.enable_autoattack(True)

	player.add_spell("Improved concentration",
		utils.spell('F1', 240, 1, utils.spell_type.self))
	player.add_spell("Wind walk",
		utils.spell('7', 400, 1.5, utils.spell_type.self))
	player.add_spell("Double strafe",
		utils.spell('2', 0, 0, utils.spell_type.attack))
	player.add_spell("Charge arrow",
		utils.spell('3', 0, 0, utils.spell_type.attack))

#	player.autospell("Improved concentration",
#		utils.cast_type.every_time, [lambda dist: player.cur_sp > 70])
#	player.autospell("Wind walk",
#		utils.cast_type.every_time, [lambda dist: player.cur_sp > 100])

	player.autospell("Charge arrow",
		utils.cast_type.battle, [lambda dist: player.cur_sp > 15 and dist < 3])
	player.autospell("Double strafe",
		utils.cast_type.battle, [lambda dist: player.sp_rate() > 0.8,
		lambda dist: player.cur_sp > 12 and player.hp_rate() < 0.2])

	player.add_potion("Strawberry", utils.potion('6', 0))
	player.add_potion("Wing", utils.potion('8', 0))

#	player.autopotion("Strawberry", [lambda : player.sp_rate() < 0.3])

	return player

if __name__ == "__main__":
	player = create_player()
	time = utils.bot_time()
	error_timer = utils.error_timer()

	enemy_sprites = utils.get_sprites(enemy_path, ["spore"])
	drop_sprites = utils.get_sprites(drop_path, ["spore", "other"])

	map = utils.load_map(map_path, "pay_field_01.txt")

	while "main loop":
		foreground_win_name = win32gui.GetWindowText(win32gui.GetForegroundWindow())
		if foreground_win_name == utils.win_name:
			image = utils.get_screen()

			time.update()
			player.update(map, time.frame_time)

			drop = utils.find_sprites(image, drop_sprites, 0.85)
			enemies = []
			if len(drop) == 0 :
				enemies = utils.find_sprites(image, enemy_sprites, 0.5)

			utils.debug_draw(image, enemies + drop)

			if len(drop) > 0:
				utils.random_sleep(0.5)
				image = utils.get_screen()
				drop = utils.find_sprites(image, drop_sprites, 0.85)
				if len(drop) > 0:
					nearer_drop = utils.find_nearer(player, drop)
					player.take(map, time, error_timer, nearer_drop, wait_time = 0.35)
			elif len(enemies) > 0:
				utils.random_sleep(0.2)
				image = utils.get_screen()
				enemies = utils.find_sprites(image, enemy_sprites, 0.5)
				if len(enemies) > 0:
					nearer_enemy = utils.find_nearer(player, enemies)
					player.attack(map, time, error_timer, nearer_enemy, wait_time = 0.1)
			else :
				map.move(player, time.frame_time, 0.03)
				error_timer.refresh()

		if cv2.waitKey(25) & 0xFF == ord("q"):
			cv2.destroyAllWindows()
			break
