from .helper import *


class Board:
    def __init__(self, env):
        if env.BOARD_SIZE == 5: # small
            self.goals = {
                1: np.arange(5),
                2: np.arange(20, 25)}
        else:
            self.goals = {
                1: np.arange(9),
                2: np.arange(72, 81)}

        self.update_possible_ilocs(env)

    def update_possible_ilocs(self, env):
        self.possible_ilocs = {
            1: env.pawn.movable_ilocs[1] + env.fence.placeable_ilocs[1],
            2: env.pawn.movable_ilocs[2] + env.fence.placeable_ilocs[2]}
        if env.fence.remaining_num[1] == 0:
            self.possible_ilocs[1] = [self.get_shortest_iloc(env, 1)]
        elif env.fence.remaining_num[2] == 0:
            self.possible_ilocs[2] = [self.get_shortest_iloc(env, 2)]

    def get_shortest_iloc(self, env, player_num):
        current_node = get_current_node(env, player_num)
        graph = self.get_graph_with_goal_node(env, player_num)
        shortest_distance = np.inf
        for movable_iloc in env.pawn.movable_ilocs[player_num]:
            movable_node = get_node_from_iloc(env, movable_iloc[0],
                movable_iloc[1])
            distance = nx.dijkstra_path_length(graph, movable_node, 'goal') - 1
            if distance < shortest_distance:
                next_node = movable_node
                shortest_distance = distance
        next_iloc = get_ilocs_from_nodes(env, [next_node])[0]
        return [next_iloc[0], next_iloc[1]]

    def get_shortest_distance(self, env, player_num):
        current_node = get_current_node(env, player_num)
        graph = self.get_graph_with_goal_node(env, player_num)
        shortest_distance = nx.dijkstra_path_length(
            graph, current_node, 'goal') - 1
        return shortest_distance

    def get_graph_with_goal_node(self, env, player_num):
        graph = env.graph.copy()
        graph.add_node('goal')
        graph.add_edges_from(
            [(i, 'goal') for i in env.board.goals[player_num]])
        return graph

    def judge_shortest(self, env, current_node, goal, shortest_distance):
        shortest = False
        distance = -1
        try:
            distance = nx.dijkstra_path_length(env.graph, current_node, goal)
        except:
            pass
        if distance >= 0:
            if distance < shortest_distance:
                shortest = True
        return shortest
