import copy
import itertools
import json
import time

from flask import Flask, Response
from flask import jsonify, redirect, render_template, request, url_for
import networkx as nx
import numpy as np

def get_clicked_iloc(json_request):
    iloc = json_request['iloc']
    row = int(iloc.split(',')[0])
    col = int(iloc.split(',')[1])
    return row, col


def get_node_from_iloc(env, row, col):
    node_num = int(env.BOARD_SIZE * (row //2) + (col // 2))
    return node_num


def get_ilocs_from_nodes(env, nodes):
    ilocs = []
    for node in nodes:
        row = int(2 * (node // env.BOARD_SIZE))
        col = int(2 * (node - (node // env.BOARD_SIZE) * env.BOARD_SIZE))
        iloc = (row, col)
        ilocs.append(iloc)
    return ilocs


def get_current_node(env, player_num):
    iloc = env.pawn.ilocs[player_num]
    return get_node_from_iloc(env, iloc[0], iloc[1])


def get_opponent_num(player_num):
    opponent_num = {1: 2, 2: 1}[player_num]
    return opponent_num


def get_opponent_node(env, player_num):
    opponent_num = get_opponent_num(player_num)
    iloc = env.pawn.ilocs[opponent_num]
    return get_node_from_iloc(env, iloc[0], iloc[1])


def get_goal_node_nums(env, player_num):
    if player_num == 1:
        return np.arange(0, env.BOARD_SIZE)
    else:
        return np.arange(env.BOARDSIZE * (env.BOARD_SIZE - 1),
            env.BOARD_SIZE ** 2)


def judge_done(env):
    if (1 in env.screen[0] or 2 in env.screen[2 * env.BOARD_SIZE - 2]):
        env.done = True

    # for mcts
    elif env.fence.remaining_num[1] == 0 and env.fence.remaining_num[2] == 0:
        env.done = True

    return env.done


def get_reward(env):
    # TODO: should be changed
    if env.done:
        if env.player_in_turn in env.screen[0] or \
                env.player_in_turn in env.screen[2 * env.BOARD_SIZE - 2]:
            reward = 1
        else:
            opponent_num = get_opponent_num(env.player_in_turn)
            player_distance = env.board.get_shortest_distance(env,
                env.player_in_turn)
            opponent_distance = env.board.get_shortest_distance(env,
                opponent_num)
            if player_distance <= opponent_distance:
                reward = 1
            else:
                reward = -1
    else:
        reward = 0
    return reward


def get_node_row_num(env, node_num):
    return node_num // env.BOARD_SIZE # 0, 1, ..., 8


def get_node_nums_from_node_row_num(env, node_row_num):
    return np.arange(env.BOARD_SIZE * node_row_num,
        env.BOARD_SIZE * node_row_num + env.BOARD_SIZE)


def get_position_from_action_index(action_index):
    # TODO: add 9x9 version
    boundary_list = [0, 9, 13, 22, 26, 35, 39, 48, 52, 57]
    row = 0
    for i, boundary in enumerate(boundary_list):
        if action_index < boundary:
            row = i - 1
            boundary = boundary_list[i - 1]
            break
    if row == 8:
        col = 2 * (action_index - boundary)
    elif row % 2 == 1:
        col = 2 * (action_index - boundary)
    else:
        col = action_index - boundary
    return (row, col)


def get_action_index_from_position(row, col):
    # TODO: add 9x9 version
    boundary_list = [0, 9, 13, 22, 26, 35, 39, 48, 52]
    action_index = boundary_list[row]
    if row % 2 == 0:
        if row == 8:
            action_index += (col // 2)
        else:
            action_index += col
    else:
        action_index += (col // 2)
        action_index = int(action_index)
    return action_index


def get_state(env):
    """ return state
    Args: env

    Returns: state
        9 x 9: 23 x 17 x 17
        5 x 5: 13 x 9 x 9
    """
    if env.BOARD_SIZE == 5:
        channel_num = 3 + 5 * 2
        start_index = 8
    else:
        channel_num = 3 + 10 * 2
        start_index = 13
    state = np.zeros((channel_num, env.BOARD_SIZE * 2 - 1,
        env.BOARD_SIZE * 2 - 1))

    # channel0: current player
    state[0][np.where(env.screen == env.player_in_turn)[0][0],
        np.where(env.screen == env.player_in_turn)[1][0]] = 1

    # channel1: opponent player
    opponent_player = {2: 1, 1: 2}[env.player_in_turn]
    state[1][np.where(env.screen == opponent_player)[0][0],
        np.where(env.screen == opponent_player)[1][0]] = 1

    # channel2: fence
    state[2][np.where(env.screen == 4)] = 1
    state[2][np.where(env.screen == 5)] = 1

    # channel3 - channel7 (or channel3 - channel12): current remaining num
    for i in range(3, 3 + env.fence.remaining_num[env.player_in_turn]):
        state[i] = 1

    # channel8 - channel12 (or channel13 - channel22): opponent remaining num
    for i in range(start_index,
            start_index + env.fence.remaining_num[opponent_player]):
        state[i] = 1
    return state
