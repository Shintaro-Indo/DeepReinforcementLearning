from .helper import *


class Pawn:
    def __init__(self, env):
        if env.BOARD_SIZE == 5: # small
            self.ilocs = {
                1: (8, 4),
                2: (0, 4)}

            self.movable_ilocs = {
                1: [(6, 4), (8, 2), (8, 6)],
                2: [(0, 2), (0, 6), (2, 4)]}
        else:
            self.ilocs = {
                1: (16, 8),
                2: (0, 8)}
            self.movable_ilocs = {
                1: [(14, 8), (16, 6), (16, 10)],
                2: [(0, 6), (0, 10), (2, 8)]}

    def update_current_ilocs(self, player_num, row, col):
        self.ilocs[player_num] = (row, col)

    def update_movable_ilocs(self, env):
        self.movable_ilocs = {
            1: self.get_movable_ilocs(env, player_num=1),
            2: self.get_movable_ilocs(env, player_num=2)}

        # cast to int for jsonify
        if len(self.movable_ilocs[1]) > 0:
            for i in range(len(self.movable_ilocs[1])):
                row = int(self.movable_ilocs[1][i][0])
                col = int(self.movable_ilocs[1][i][1])
                self.movable_ilocs[1][i] = (row, col)

    def get_movable_ilocs(self, env, player_num):
        current_node = get_current_node(env, player_num)
        opponent_node = get_opponent_node(env, player_num)
        movable_nodes = list(nx.all_neighbors(env.graph, current_node))
        for movable_node in movable_nodes:
            if opponent_node == movable_node: # next to
                difference = opponent_node - current_node
                node_jump_to = opponent_node + difference
                # no fence nor edge
                if node_jump_to in nx.all_neighbors(env.graph, opponent_node):
                    movable_nodes.append(node_jump_to)
                # fence or edge
                else:
                    movable_nodes += nx.all_neighbors(env.graph, opponent_node)
                    movable_nodes.remove(current_node)
                movable_nodes.remove(opponent_node)
        movable_ilocs = list(get_ilocs_from_nodes(env, movable_nodes))
        return movable_ilocs
