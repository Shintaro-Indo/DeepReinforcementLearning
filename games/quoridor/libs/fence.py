from .helper import *


class Fence:
    def __init__(self, env):
        if env.BOARD_SIZE == 5:
            self.remaining_num = {
                1: 5,
                2: 5}
        else:
            self.remaining_num = {
                1: 10,
                2: 10}

        self.initial_placeble_ilocs = list(list(itertools.product(env.EVENS_P,
            env.ODDS)) + list(itertools.product(env.ODDS, env.EVENS_P)))

        # ilocs where a fence can be placed without overlapping each other
        self.non_overlapping_ilocs = list(list(itertools.product(env.EVENS_P,
            env.ODDS)) + list(itertools.product(env.ODDS, env.EVENS_P)))

        # not overlap nor block
        self.placeable_ilocs = {
            0: copy.deepcopy(self.non_overlapping_ilocs), # if fence remain > 0
            1: copy.deepcopy(self.non_overlapping_ilocs),
            2: copy.deepcopy(self.non_overlapping_ilocs)}

        # cast to int for jsonify
        for i in range(len(self.placeable_ilocs[1])):
            row = int(self.placeable_ilocs[1][i][0])
            col = int(self.placeable_ilocs[1][i][1])
            self.placeable_ilocs[1][i] = (row, col)

    def update_remaining_num(self, player_num):
        self.remaining_num[player_num] -= 1

    def get_edges_being_removed(self, env, row, col):
        """
        get edge nums which (row, col) fence will
        """
        if row % 2 == 0: # place vertcally
            edge_1 = (get_node_from_iloc(env, row, col - 1),
                get_node_from_iloc(env, row, col + 1))
            edge_2 = (get_node_from_iloc(env, row + 2, col - 1),
                get_node_from_iloc(env, row + 2, col + 1))
        else: # place horizontally
            edge_1 = (get_node_from_iloc(env, row - 1, col),
                get_node_from_iloc(env, row + 1, col))
            edge_2 = (get_node_from_iloc(env, row - 1, col + 2),
                get_node_from_iloc(env, row + 1, col + 2))
        return edge_1, edge_2

    def update_placeable_ilocs(self, env, row, col):
        self.update_non_overlapping_ilocs(row, col)
        if (self.remaining_num[1] > 0) | (self.remaining_num[2] > 0):
            self.remove_blocking_ilocs(env)
        for player_num in [1, 2]:
            if self.remaining_num[player_num] > 0: # fence remain
                self.placeable_ilocs[player_num] = copy.deepcopy(
                    self.placeable_ilocs[0])
            else: # no fence
                self.placeable_ilocs[player_num] = []
        # cast to int for jsonify
        if len(self.placeable_ilocs[1]) > 0:
            for i in range(len(self.placeable_ilocs[1])):
                row = int(self.placeable_ilocs[1][i][0])
                col = int(self.placeable_ilocs[1][i][1])
                self.placeable_ilocs[1][i] = (row, col)

    def update_non_overlapping_ilocs(self, row, col):
        if row % 2 == 0: # place vertcally
            overlapping_ilocs = [(row - 2, col), (row, col), (row + 1, col - 1),
                (row + 2, col)]
        else: # place horizontally
            overlapping_ilocs = [(row - 1, col + 1), (row, col - 2), (row, col),
                (row, col + 2)]

        self.non_overlapping_ilocs = list(
            set(self.non_overlapping_ilocs) - set(overlapping_ilocs))

    def remove_blocking_ilocs(self, env):
        """
        rid placeable_ilocs[0] of ilocs which block all routes to goals
        """
        blocking_ilocs = []
        for player_num in [1, 2]:
            current_node = get_current_node(env, player_num)
            graph = env.graph.copy()
            graph.add_node('goal')
            graph.add_edges_from(
                [(i, 'goal') for i in env.board.goals[player_num]])
            route = nx.shortest_path(graph, current_node, 'goal')[:-1]
            ilocs = self.get_ilocs_of_removing_edges(env,
                [(route[i], route[i + 1]) for i in range(len(route) - 1)])
            for iloc in set(ilocs) & set(self.non_overlapping_ilocs):
                edge_1, edge_2 = self.get_edges_being_removed(env, iloc[0],
                    iloc[1])
                graph_tmp = graph.copy()
                graph_tmp.remove_edges_from([edge_1, edge_2])
                if not nx.has_path(graph_tmp, current_node, 'goal'):
                    blocking_ilocs.append(iloc)
        self.placeable_ilocs[0] = list(set(self.non_overlapping_ilocs)
            - (set(blocking_ilocs)))

    def get_ilocs_of_removing_edges(self, env, edges):
        ilocs = []
        for edge in edges:
            first_node = np.min(edge)
            second_node = np.max(edge)
            if (second_node - first_node) == 1: # vertical fence
                row = first_node // env.BOARD_SIZE * 2
                col = (first_node % env.BOARD_SIZE) * 2 + 1
                if row == 0:
                    ilocs.extend([(row, col)]) # extend: append list
                elif row == env.BOARD_SIZE * 2 - 2:
                    ilocs.extend([(row - 2, col)])
                else:
                    ilocs.extend([(row - 2, col), (row, col)])
            else: # horizontal fence
                row = first_node // env.BOARD_SIZE * 2 + 1
                col = first_node % env.BOARD_SIZE * 2
                if col == 0:
                    ilocs.extend([(row, col)])
                elif col == env.BOARD_SIZE * 2 - 2:
                    ilocs.extend([(row, col - 2)])
                else:
                    ilocs.extend([(row, col - 2), (row, col)])
        return ilocs
