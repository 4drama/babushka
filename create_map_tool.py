import lib.utils as utils

import tkinter
import os

map_path = "./data/map/"

map = utils.map()

root = tkinter.Tk()
root.title("Create map tool")
root.geometry("800x800")

canvas = tkinter.Canvas(root, width=800, height=770, bg='#484')
canvas.place(x = 0, y = 30)

def get_x():
	return utils.game_process.read_int(utils.x_player_position_addr)

def get_y():
	return utils.game_process.read_int(utils.y_player_position_addr)

Point_labels = []
label1 = tkinter.Label(text="You", fg="#eee", bg="#333")

set_position_button = tkinter.Button(text = 'set_position')
set_position_button.place(x = 10, y = 10, width = 80, height = 20)

first_entry = tkinter.Entry()
second_entry = tkinter.Entry()
first_entry.place(x = 100, y = 10, width = 40, height = 20)
second_entry.place(x = 150, y = 10, width = 40, height = 20)

set_chain_button = tkinter.Button(text = 'set_chain')
set_chain_button.place(x = 200, y = 10, width = 80, height = 20)

save_button = tkinter.Button(text = 'save')
save_button.place(x = 500, y = 10, width = 80, height = 20)

save_entry = tkinter.Entry()
save_entry.place(x = 590, y = 10, width = 200, height = 20)

def set_pos(ev):
	number = len(map.nodes)
	map.add_node(get_x(), get_y())

	lab = tkinter.Label(text=number, fg="#eee", bg="#e33")
	lab.place(x = get_x() * 2, y = 800 - get_y() * 2)
	Point_labels.append(lab)

def set_chain(ev):
	first = int(first_entry.get())
	second = int(second_entry.get())
	map.add_chain(first, second)

	canvas.create_line(
		map.nodes[first].pos.x * 2, 770 - map.nodes[first].pos.y * 2,
		map.nodes[second].pos.x * 2, 770 - map.nodes[second].pos.y * 2, width = 3)

def save(ev):
	filename = save_entry.get()
	map.save_map(map_path, filename + ".txt")

def update():
	label1.place(x = get_x() * 2, y = 800 - get_y() * 2)

	root.after(1000, update)

set_position_button.bind("<Button-1>", set_pos)
set_chain_button.bind("<Button-1>", set_chain)
save_button.bind("<Button-1>", save)

update()

root.mainloop()
