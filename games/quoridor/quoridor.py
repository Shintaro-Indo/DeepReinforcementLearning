import copy
import logging

import numpy as np

from .libs.board import Board
from .libs.fence import Fence
from .libs.helper import *
from .libs.pawn import Pawn
from .quoridor_env import QuoridorEnv


class Quoridor:

	def __init__(self):
		# from deep quoridor
		self._env = QuoridorEnv(small=True)

		self.currentPlayer = 1 # {1: 1, 2: -1}[self._env.player_in_turn] # 1 or -1
		self.gameState = QuoridorState(env=self._env, playerTurn=1)

		self.actionSpace = np.zeros(self._env.BOARD_SIZE ** 2 +
			((self._env.BOARD_SIZE - 1) ** 2) * 2)

		self.pieces = {
            '0': '□',
            '1': '◆',
            '-1': '●',
			'2': '●',
            '3': ' ',
            '4': 'ー',
            '5': '｜',}

		rows = self._env.BOARD_SIZE * 2 - 1
		cols = self._env.BOARD_SIZE * 2 - 1
		channels = 13 if self._env.small else 23
		self.grid_shape = (rows, cols)
		self.input_shape = (channels, rows, cols)
		self.name = 'quoridor'
		self.state_size = len(self.gameState.binary)
		self.action_size = len(self.actionSpace)

	def reset(self):
		"""
		Reset self.gameState and self.currentPlayer

		Args:
			self.count_nonzero

		Returns:
			self.gameState: object
		"""
		self._env.reset()
		self.gameState = QuoridorState(env=self._env, playerTurn=1)
		self.currentPlayer = 1
		return self.gameState

	def step(self, action):
		"""
		Update next_state, value, done, self.gameState, self.currentPlayer,
			self._env

		Args:
			action

		Returns:
			((next_state, value, done, info)) # value: reward?, info: None
		"""
		# print('step')
		print(f'Player: {self.currentPlayer}')
		print(f'Allowed: {sorted(self.gameState.allowedActions)}')

		row, col = get_position_from_action_index(action)
		_action = (row, col)
		print(f'Action: {_action}')

		next_state, value, done = self.gameState.takeAction(action)

		self._env.step(_action, self._env.player_in_turn)
		print(np.array(next_state.board).reshape(9, 9))
		print(f'Remaining nums: {next_state.remainingNums}')

		self.gameState = next_state
		self.currentPlayer = - self.currentPlayer
		info = None
		return ((next_state, value, done, info))

	def identities(self, state, actionValues):
		"""
		Get the id of (state and actionValues) and mirror-reversed one

		Args:
			state, actionValues

		Returns:
			identities: [(state, AV), (mirror-state, mirror-AV)]
		"""
		identities = [(state, actionValues)]

		env_tmp = copy.deepcopy(self._env)
		env_tmp.screen = env_tmp.screen[:, ::-1]

		currentAV = actionValues
		cA = copy.deepcopy(currentAV)
		currentAV = np.array([
			cA[8], cA[7], cA[6], cA[5], cA[4],
			 	cA[3], cA[2], cA[1], cA[0],
			cA[12], cA[11], cA[10], cA[9],
			cA[21], cA[20], cA[19], cA[18], cA[17],
				cA[16], cA[15], cA[14],cA[13],
			cA[25], cA[24], cA[23], cA[22],
			cA[34], cA[33], cA[32], cA[31], cA[30],
				cA[29], cA[28], cA[27],cA[26],
			cA[38], cA[37], cA[36], cA[35],
			cA[47], cA[46], cA[45], cA[44], cA[43],
				cA[42], cA[41], cA[40],cA[39],
			cA[51], cA[50], cA[49],cA[48],
			cA[56], cA[55], cA[54], cA[53], cA[52], cA[51]])

		identities.append((QuoridorState(env_tmp, state.playerTurn), currentAV))

		return identities


class QuoridorState():
	def __init__(self, env, playerTurn):
		self._env = env
		self.board = copy.deepcopy(self._env.screen.astype(int))
		self.board
		self.board = self.board.flatten()
		self.pieces = {
            '0': '□',
            '1': '◆',
            '-1': '●',
			'2': '●',
            '3': ' ',
            '4': '-',
            '5': '|',}
		self.winners = []
		self.playerTurn = playerTurn# {1: 1, 2: -1}[self._env.player_in_turn]
		self.binary = self._binary() # (81*23,). [current player, opponent]
		self.id = self._convertStateToId() # e.g. '010..0' (length: 81*23)
		self.allowedActions = self._allowedActions() # list of allowd index
		self.isEndGame = self._checkForEndGame() # 1 or 0
		self.value = self._getValue() # (0, 0, 0) or (-1, -1, 1)?
		self.score = self._getScore() # (0, 0) or (-1, 1)?

		self.remainingNums = copy.deepcopy(env.fence.remaining_num)

	def _allowedActions(self):
		"""
		Get the list of allowd actions

		Args:
			None

		Returns:
			allowd
		"""
		player_num = {1: 1, -1: 2}[self.playerTurn] # player_in_turn
		allowed_ilocs = self._env.board.possible_ilocs[player_num]
		allowed = []
		for iloc in allowed_ilocs:
			action_index = get_action_index_from_position(iloc[0], iloc[1])
			allowed.append(action_index)
		return allowed

	def _binary(self):
		"""
		Get the list of current player position and opponent position

		Args:
			None

		Return:
			binary: [current_player_position, other_position]
		"""
		binary = copy.deepcopy(self._env.state.astype(int))
		binary = binary.flatten() # 1053 or 6647

		return (binary)

	def _convertStateToId(self):
		"""
		Get the id of state

		Args:
			None

		Returns:
			id: e.g. '010...010...0' (length: 84)
		"""
		position = copy.deepcopy(self._env.state.astype(int))
		position = position.flatten()

		id = ''.join(map(str, position))

		return id

	def _checkForEndGame(self):
		"""
		Get whether the game is ended

		Args:
			None

		Returns:
			1 (ended) or 0 (not ended)
		"""
		done = self._env.done
		if done:
			return 1
		else:
			return 0

	def _getValue(self):
		"""
		Get the value of the state for the current player
		i.e. if the previous player played a winning move, you lose

		Args:
			None

		Returns:
			(0, 0, 0) or (-1, -1, 1) # (current?, current, opponent)
		"""
		done = self._env.done
		if done:
			# TODO* check
			return (1, 1, -1)
		else:
			return (0, 0, 0)

	def _getScore(self):
		"""
		Get tuple of current player and opponent value

		Args:
			None

		Return:
			(current player value, opponent value)
		"""
		tmp = self.value
		return (tmp[1], tmp[2])

	def takeAction(self, action):
		"""
		Get newState, value and done updated by the given action

		Args:
			action

		Returns:
			(newState, value, done)
		"""
		row, col = get_position_from_action_index(action)
		_action = (row, col)

		env_tmp = copy.deepcopy(self._env)

		player_num = {1: 1, -1: 2}[self.playerTurn]
		env_tmp.step(_action, player_num)

		newScreen = env_tmp.screen

		newState = QuoridorState(env_tmp, -self.playerTurn) # updated remainings

		value = 0
		done = 0

		if env_tmp.done:
			value = newState.value[0]
			done = 1

		# for debug
		# print('takeAction')
		# print(f'Player: {newState.playerTurn}')
		# print(f'Allowed: {sorted(newState.allowedActions)}')
		# print(f'Action: {_action}')
		# print('Screen')
		# print(newScreen)
		# print(f'Remaining nums: {newState.remainingNums}')
		# print('Done: ', done)
		# print()

		return (newState, value, done)

	def render(self, logger):
		"""
		Logging

		Args:
			logger

		Returns:
			None
		"""
		screen_size = self._env.BOARD_SIZE * 2 - 1
		for r in range(screen_size):
			logger.info([self.pieces[str(int(x))] for x in
				self.board[r * screen_size: r * screen_size + screen_size ]])

		logger.info('--------------')
