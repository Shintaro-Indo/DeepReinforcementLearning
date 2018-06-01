import numpy as np

from .libs.board import Board
from .libs.fence import Fence
from .libs.helper import *
from .libs.pawn import Pawn

class QuoridorEnv:
    def __init__(self, small=False):
        self.small = small
        self.reset()

    def reset(self):
        """
        initialize the game
        """
        # constants
        if self.small:
            self.BOARD_SIZE = 5 # 5 squares
            self._BOARD_SIZE = 9 # 5 squares + 4 grooves
            self.ODDS = np.arange(1, self._BOARD_SIZE - 1, 2) # 1-7(placeable)
            self.EVENS_P = np.arange(0, self._BOARD_SIZE - 1, 2) # 0-6(plaeable)
            self.EVENS_A = np.arange(0, self._BOARD_SIZE, 2) # 0-8(action)
        else:
            self.BOARD_SIZE = 9 # 9 squaress
            self._BOARD_SIZE = 17 # 9 squares + 8 grooves
            self.ODDS = np.arange(1, self._BOARD_SIZE - 1, 2) # 1-15
            self.EVENS_P = np.arange(0, self._BOARD_SIZE - 1, 2) # 0-14
            self.EVENS_A = np.arange(0, self._BOARD_SIZE, 2) # 0-16

        # variables

        self.time_step = 1
        self.player_in_turn = 1
        self.done = False

        self.pawn = Pawn(self)
        self.fence = Fence(self)

        ## graph
        self.graph = nx.Graph()
        self.graph.add_nodes_from(np.arange(self.BOARD_SIZE * self.BOARD_SIZE))
        for col in range(self.BOARD_SIZE - 1): # add vertival edges
            self.graph.add_edges_from([(node_num, node_num + self.BOARD_SIZE)
                for node_num in range(col * self.BOARD_SIZE,
                    col * self.BOARD_SIZE + self.BOARD_SIZE)])
        for row in range(self.BOARD_SIZE): # add horizontal edges
            self.graph.add_edges_from([(node_num, node_num + 1) for node_num in
                range(row * self.BOARD_SIZE,
                    row * self.BOARD_SIZE + self.BOARD_SIZE - 1)])

        ## screen
        self.screen = np.zeros((self._BOARD_SIZE, self._BOARD_SIZE))

        ### groove
        self.screen[self.ODDS, :] = 3 # odd rows
        self.screen[:, self.ODDS] = 3 # odd cols

        ### player
        self.screen[self.pawn.ilocs[1]] = 1
        self.screen[self.pawn.ilocs[2]] = 2

        ## state
        self.state = get_state(self)

        ## board
        self.board = Board(self)

        ## history
        # hash_state = get_hash_state(self)
        self.history = [get_hash_state(self)]

        return self.state

    def step(self, action, player_num):
        """
        update env

        Args:
            action: (row, column)
            player_num: 1 or 2

        Return:
            next_state, reward, done, info
        """
        row = action[0]
        col = action[1]

        # move or place
        if row % 2 == 0 and col % 2 == 0: # move
            self.move_pawn(row, col, player_num)
        else: # place
            self.place_fence(row, col, player_num)

        self.time_step += 1
        self.player_in_turn = {1: 2, 2: 1}[self.player_in_turn]
        next_state = get_state(self)
        self.state = next_state
        done = judge_done(self)
        reward = get_reward(self)
        info = None

        hash_state = get_hash_state(self)
        self.history.append(hash_state)

        return next_state, reward, done, info


    def move_pawn(self, row, col, player_num):
        # update screen
        self.screen[np.where(self.screen == player_num)] = 0 # leave
        self.screen[row, col] = player_num # move

        # update pawn
        self.pawn.update_current_ilocs(player_num, row, col)
        self.pawn.update_movable_ilocs(self)

        # update fence
        self.fence.update_placeable_ilocs(self, row, col)

        # updat board
        self.board.update_possible_ilocs(self)

    def place_fence(self, row, col, player_num):
        # update screen
        if row % 2 == 1: # place horizontally
            self.screen[row, col: col + 3] = 4
        else: # place vertically
            self.screen[row: row + 3, col] = 5

        # update graph
        edge_1, edge_2 = self.fence.get_edges_being_removed(self, row, col)
        self.graph.remove_edges_from([edge_1, edge_2])

        # update fence
        self.fence.update_remaining_num(player_num)
        self.fence.update_placeable_ilocs(self, row, col) # self: env

        # uodate pawn
        self.pawn.update_movable_ilocs(self)

        # update board
        self.board.update_possible_ilocs(self)

    def take_action(self, action, player_num):
        """ to prepend recursion in update_possible_ilocs
        """
        # update screen
        self.screen[np.where(self.screen == player_num)] = 0 # leave
        self.screen[action[0], action[1]] = player_num # move
