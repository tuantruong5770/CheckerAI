from random import randint
from BoardClasses import Move
from BoardClasses import Board
import math
import time
import os
import copy
import threading
import multiprocessing as mp
#The following part should be completed by students.
#Students can modify anything except the class name and exisiting functions and varibles.

C = math.sqrt(math.sqrt(2)) # Exploration Parameter
# NS = 100
# TS = 15 # time for each mcts
# minVisit = 15
num_thread = len(os.sched_getaffinity(0)) - 1
queue = mp.Queue()

class TreeNode:
    def __init__(self, move, player, parent=None):
        self.move = move
        self.parent = parent
        self.child_node = []
        self.simulation = 0
        self.win = 0
        self.player = player

    def uct(self):
        if self.simulation == 0:
            return 9999
        if self.parent:
            return self.winrate() + C * math.sqrt(math.log(self.parent.simulation)/self.simulation)

    def winrate(self):
        if self.simulation == 0:
            return 0
        return self.win/self.simulation

    def __repr__(self):
        return "TreeNode: " + str(self.move) + " player: " + str(self.player)



class StudentAI():

    def __init__(self,col,row,p):
        self.col = col
        self.row = row
        self.p = p
        self.boards = []
        for i in range(num_thread + 1):
            self.boards.append(Board(col, row, p))
            self.boards[i].initialize_game()
        self.color = ''
        self.opponent = {1:2,2:1}
        self.color = 2
        self.mcts_trees = [TreeNode(None, self.color) for i in range(num_thread + 1)]
        self.sim_total = 0
        self.sim_counter = 0
        self.TS = 12
        self.minVisit = 15
        if col > 7 and row > 7:
            self.TS = 12
            self.minVisit = 15
        print(len(os.sched_getaffinity(0)))

    def get_move(self,move):
        """
        Return best next move
        :param move: Previous move made by opponent
        :return: AI's move
        """
        if len(move) != 0:
            # print("|" + str(move) + "|")
            self.confirm_move(move, self.opponent[self.color])
            self.update_node(move)
            #print("Player", self.opponent[self.color], "make move", move)
        else:
            self.color = 1
            for i in range(num_thread + 1):
                self.mcts_trees[i].player = self.color
        self.run_mcts(self.TS, True)
        #print("avg sim time:", self.sim_total / self.sim_counter)
        move = self.pick_move()
        self.confirm_move(move, self.color)
        self.update_node(move)

        # Expand in case new nodes have no child
        temp_moves = self.boards[0].get_all_possible_moves(self.opponent[self.color])
        for node in self.mcts_trees:
            if len(node.child_node) == 0:
                for t_move in temp_moves:
                    for eachmove in t_move:
                        node.child_node.append(TreeNode(eachmove, self.opponent[node.player], node))

        # print("Player", self.color, "make move", move.move, "with a winrate of", move.winrate(), "simulated", move.simulation)
        return move


    def update_node(self, move):
        """
        Find index of node to udpate
        :param current_node: current node
        :param move: move to update
        :return: index of child
        """
        index = 0
        if len(self.mcts_trees[0].child_node) != 0:
            for i, child in enumerate(self.mcts_trees[0].child_node):
                if str(child.move) == str(move):
                    index = i
                    break
            for i in range(len(self.mcts_trees)):
                self.mcts_trees[i] = self.mcts_trees[i].child_node[index]
                self.mcts_trees[i].parent = None

    def confirm_move(self, move, player):
        """
        Make move
        :return: Nun
        """
        for board in self.boards:
            board.make_move(move, player)

    def pick_move(self):
        """
        Pick move base on win rate
        :return: Move object
        """
        child_node_evaluate = []
        num_child = len(self.mcts_trees[0].child_node)
        # print(self.mcts_trees[0].move)
        # print(list(i.move for i in self.mcts_trees[0].child_node))
        """
        Adding num_sim and num_win for each child node from all tree
        Store in child_node_list list
        """
        for i in range(num_child):
            num_sim = 0
            num_win = 0
            for j in range(num_thread + 1):
                num_sim += self.mcts_trees[j].child_node[i].simulation
                num_win += self.mcts_trees[j].child_node[i].win
            """
            Change for different picking method
            Currently: win rate
            """

            child_node_evaluate.append(num_win/(num_sim if num_sim else 1))
        best = child_node_evaluate[0]
        index = 0
        for i, item in enumerate(child_node_evaluate):
            if best < item:
                best = item
                index = i
        return self.mcts_trees[0].child_node[index].move



    def run_mcts(self, number_sim, time_sim=False):
        """
        Running mcts with clone trees using multithreading
        :param number_sim: number of simulation
        :return: None
        """
        bt = time.time()
        processes = []
        for i in range(num_thread):
            p = mp.Process(target=self.mcts_wrapper, args=(self.mcts_trees[i], number_sim, time_sim, self.boards[i]))
            processes.append(p)
            p.start()
        # print(processes)
        '''
        for main process
        '''
        if time_sim:
            count = 0
            while time.time() - bt < number_sim:
                count += 1
                self.mcts(self.mcts_trees[-1], self.boards[-1])
            print(count)
        else:
            for i in range(number_sim):
                self.mcts(self.mcts_trees[-1], self.boards[-1])
        print("Time taken main:", time.time() - bt)

        i = 0
        while True:
            running = any(p.is_alive() for p in processes)
            while not queue.empty():
                self.mcts_trees[i] = queue.get()
                i += 1
            if not running:
                break
        for p in processes:
            # print("initiated")
            p.join()
            # print(p, "JOINED")
        # print("JOINED")

        for p in processes:
            if p.is_alive():
                p.terminate()
                # print("terminated bitch")
            # else:
            #     print("exit code", str(p.exitcode))
        # for p in processes:
        #     p.kill()
        # print("finished processes")
        # self.mcts_trees = [queue.get() for p in processes]
        # print(self.mcts_trees[0].child_node[0])


    def mcts_wrapper(self, node, number_sim, time_sim, board):
        """
        Wrapper for self.mcts
        :param node: current node
        :param number_sim: number of simulation
        :return: None
        """
        bt = time.time()
        # print("going in")
        if time_sim:
            count = 0
            while time.time()-bt < number_sim:
                count += 1
                self.mcts(node,board)
            print(count)
        else:
            for i in range(number_sim):
                self.mcts(node, board)
        # print("FUCK ye")
        # for child in node.child_node:
        #     print(child.simulation, end=" | ")
        # print()
        print("Time taken:", time.time() - bt)
        queue.put(node)
        # print("putin")



    def mcts(self, node, board):
        """
        One run of Monte Carlo Tree Search using recursive
        :param node: current node
        :param board: current broad
        :return: N/A (result for recursive call)
        """
        if node.simulation >= self.minVisit:
            #print("depth:", depth)
            node.simulation += 1
            if not len(node.child_node):
                moves = board.get_all_possible_moves(node.player)
                for move in moves:
                    for eachmove in move:
                        node.child_node.append(TreeNode(eachmove, self.opponent[node.player], node))
            # proceed
            #bt = time.time()
            next = self.mcts_selection(node)
            #print("self.mcts_selection:", time.time() - bt)
            #bt = time.time()
            board.make_move(next.move, node.player)
            #print("self.board.make_move", time.time() - bt)
            #bt = time.time()
            result = board.is_win(node.player)
            #print("self.board.is_win", time.time() - bt)
            if result:
                if result == self.opponent[node.player]: node.win += 1
                elif result == node.player:
                    next.win += 1
                    next.simulation += 1
                board.undo()
                return result
                    #self.board.show_board()
            result = self.mcts(next, board)
            #bt = time.time()
            board.undo()
            #print("self.board.undo()", time.time() - bt)
            # propagate up
            if result == self.opponent[node.player]:
                node.win += 1
            return result
        else:
            bt = time.time()
            result = self.simulate(node.player, board)
            bt = time.time() - bt
            self.sim_total += bt
            self.sim_counter += 1
            #print("self.simulate", bt)
            node.simulation += 1
            if result == self.opponent[node.player]:
                node.win += 1
            #print("simulating", result)
            return result



    def mcts_selection(self, node):
        """
        Select optimal UCB node
        :param node: current node
        :return: child node to explode (based on uct value)
        """
        current = node.child_node[0]
        for child in node.child_node:
            #print(current.uct())
            if current.uct() < child.uct():
                current = child
        #print("player", node.player, "pick", current.move)
        return current



    def simulate(self, player, board):
        """
        Simulate checker game
        :param player: current player turn
        :param board: current board
        :return: winner (-1 for tie)
        """
        win = 0
        counter = 0
        # fake_board = Board(self.col, self.row, self.p)
        # self.copy_board(fake_board)
        # print("DIT ME TUAN")
        # board.show_board()
        #totaltime = 0
        while win == 0:
            moves = board.get_all_possible_moves(player)
            if len(moves) == 1:
                index = 0
            elif len(moves) == 0:
                win = self.opponent[player]
                break
            else:
                index = randint(0, len(moves) - 1)
            if len(moves[index]) == 1:
                inner_index = 0
            else:
                inner_index = randint(0, len(moves[index]) - 1)
            move = moves[index][inner_index]
            board.make_move(move, player)
            counter += 1
            #bt = time.time()
            if board.tie_counter >= board.tie_max:
                win = -1
            #totaltime += time.time() - bt
            #print("self.board.is_win():", time.time() - bt)
            player = self.opponent[player]

        # #print("total time is_win:", totaltime)
        # #bt = time.time()
        for i in range(counter):
            board.undo()
        # print("total time undo:", time.time() - bt)
        # print("UNDO")
        # board.show_board()print
        #print("winner", win)
        return win






    # def copy_board(self, board):
    #     """
    #     EZ game
    #     :return: ez board
    #     """
    #     board.tie_counter = self.board.tie_counter
    #     board.tie_max = self.board.tie_max
    #     #bt = time.time()
    #     board.board = copy.deepcopy(self.board.board)
    #     board.saved_move = copy.deepcopy(self.board.saved_move)
    #     #print("Deepcopying", time.time() - bt)
    #     board.black_count = self.board.black_count
    #     board.white_count = self.board.white_count








    # def is_win(self, board):
    #     """
    #     this function tracks if any player has won
    #     @param :
    #     @param :
    #     @return :
    #     @raise :
    #     """
    #     if board.tie_counter >= board.tie_max:
    #         return -1
    #     W_has_move = True
    #     B_has_move = True
    #     if len(board.get_all_possible_moves(1)) == 0:
    #         if turn != 1:
    #             B_has_move = False
    #     elif len(board.get_all_possible_moves(2)) == 0:
    #         if turn != 2:
    #             W_has_move = False
    #
    #     if W_has_move and not B_has_move:
    #         return 2
    #     elif not W_has_move and B_has_move:
    #         return 1
    #     else:
    #         return 0

