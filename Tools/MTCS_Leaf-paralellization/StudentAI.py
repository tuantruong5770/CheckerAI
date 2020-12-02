from random import randint
from BoardClasses import Move
from BoardClasses import Board
import multiprocessing as mp
import math
import time
import copy
#The following part should be completed by students.
#Students can modify anything except the class name and exisiting functions and varibles.

C = math.sqrt(math.sqrt(2)) # Exploration Parameter
NS = 1000
minVisit = 20
num_processes = 5

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
        self.board = [Board(col,row,p) for i in range(num_processes)]
        for board in self.board:
            board.initialize_game()
        self.color = ''
        self.opponent = {1:2,2:1}
        self.color = 2
        self.search_lim = 5
        self.current_node = TreeNode(None, self.color)
        self.sim_total = 0
        self.sim_counter = 0

    def get_move(self,move):
        if len(move) != 0:
            # print("|" + str(move) + "|")
            self.all_make_move(move, self.opponent[self.color])
            #print("Player", self.opponent[self.color], "make move", move)
            if len(self.current_node.child_node) != 0:
                for child in self.current_node.child_node:
                    if str(child.move) == str(move):
                        self.current_node = child
        else:
            self.color = 1
            self.current_node.player = self.color
        bt = time.time()
        for i in range(NS):
            self.mcts(self.current_node)
            #self.board.show_board()
            #print("mcts counter:", i)
        move = self.current_node.child_node[0]
        print("self.mtcs:", time.time() - bt)
        print("avg sim time:", self.sim_total / self.sim_counter)
        for child in self.current_node.child_node:
            if move.winrate() < child.winrate():
                move = child
        self.all_make_move(move.move, self.color)
        # print("Player", self.color, "make move", move.move, "with a winrate of", move.winrate(), "simulated", move.simulation)
        self.current_node = move
        temp_moves = self.board[0].get_all_possible_moves(self.opponent[self.color])
        if len(self.current_node.child_node) == 0:
            for t_move in temp_moves:
                for eachmove in t_move:
                    self.current_node.child_node.append(TreeNode(eachmove, self.opponent[self.current_node.player], self.current_node))
        return move.move

    def all_make_move(self, move, player):
        for board in self.board:
            board.make_move(move, player)

    def all_undo(self):
        for board in self.board:
            board.undo()

    def mcts(self, node):
        if node.simulation >= minVisit:
            #print("depth:", depth)
            node.simulation += num_processes
            if not len(node.child_node):
                #bt = time.time()
                moves = self.board[0].get_all_possible_moves(node.player)
                #print("self.board.get_all_possible_moves:", time.time() - bt)
                for move in moves:
                    for eachmove in move:
                        node.child_node.append(TreeNode(eachmove, self.opponent[node.player], node))
            # proceed
            #bt = time.time()
            next = self.mcts_selection(node)
            #print("self.mcts_selection:", time.time() - bt)
            #bt = time.time()
            self.all_make_move(next.move, node.player)
            #print("self.board.make_move", time.time() - bt)
            #bt = time.time()
            result = [self.board[0].is_win(node.player) * num_processes]
            #print("self.board.is_win", time.time() - bt)
            if result:
                if result == self.opponent[node.player]: node.win += num_processes
                elif result == node.player:
                    next.win += num_processes
                    next.simulation += num_processes
                self.all_undo()
                return result
                    #self.board.show_board()
            result = self.mcts(next)
            #bt = time.time()
            self.all_undo()
            #print("self.board.undo()", time.time() - bt)
            # propagate up
            for res in result:
                if res == self.opponent[node.player]:
                    node.win += 1
            return result
        else:
            bt = time.time()
            result = self.simulate_wrapper(node.player)
            bt = time.time() - bt
            self.sim_total += bt
            self.sim_counter += num_processes
            #print("self.simulate", bt)
            node.simulation += num_processes
            for res in result:
                if result == self.opponent[node.player]:
                    node.win += 1
            #print("simulating", result)
            return result



    def mcts_selection(self, node): # Select optimal UCB node
        current = node.child_node[0]
        for child in node.child_node:
            #print(current.uct())
            if current.winrate() < child.winrate():
                current = child
        #print("player", node.player, "pick", current.move)
        return current

    def simulate_wrapper(self, player):
        processes = []
        result = []
        for i in range(num_processes):
            p = mp.Process(target=self.simulate, args=(player, self.board[i], result))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        for p in processes:
            if p.is_alive():
                p.terminate()
        return result

    def simulate(self, player, board, result):
        win = 0
        counter = 0
        # fake_board = Board(self.col, self.row, self.p)
        # self.copy_board(fake_board)
        #print("DIEN")
        #fake_board.show_board()
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
        # #rint("total time undo:", time.time() - bt)
        #fake_board.show_board()
        #print("winner", win)
        result.append(win)

    #
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

