def create_pay_field_01():
	map = utils.map()
	map.add_node(289, 341)	#0
	map.add_node(348, 315)	#1
	map.add_node(326, 252)	#2
	map.add_node(361, 232)	#3
	map.add_node(322, 218)	#4
	map.add_node(301, 168)	#5
	map.add_node(336, 133)	#6
	map.add_node(303, 217)	#7
	map.add_node(285, 201)	#8
	map.add_node(259, 252)	#9
	map.add_node(220, 252)	#10
	map.add_node(195, 218)	#11
	map.add_node(228, 176)	#12
	map.add_node(254, 168)	#13
	map.add_node(276, 122)	#14

	map.add_chain(0, 1)
	map.add_chain(1, 2)
	map.add_chain(2, 3)
	map.add_chain(3, 4)
	map.add_chain(4, 5)
	map.add_chain(5, 6)
	map.add_chain(4, 7)
	map.add_chain(7, 8)
	map.add_chain(8, 9)
	map.add_chain(9, 10)
	map.add_chain(10, 11)
	map.add_chain(11, 12)
	map.add_chain(12, 13)
	map.add_chain(13, 14)
	return map
