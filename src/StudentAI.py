from random import randint
from BoardClasses import Move
from BoardClasses import Board
import math
import time
import copy
#The following part should be completed by students.
#Students can modify anything except the class name and exisiting functions and varibles.

C = math.sqrt(math.sqrt(2)) # Exploration Parameter
NS = 1000
minVisit = 20
num_processes = 6

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
        self.board = Board(col,row,p)
        self.board.initialize_game()
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
            self.board.make_move(move, self.opponent[self.color])
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
            if move.uct() < child.uct():
                move = child
        self.board.make_move(move.move, self.color)
        # print("Player", self.color, "make move", move.move, "with a winrate of", move.winrate(), "simulated", move.simulation)
        self.current_node = move
        return move.move


    def mcts(self, node):
        if node.simulation >= minVisit:
            #print("depth:", depth)
            node.simulation += 1
            if not len(node.child_node):
                #bt = time.time()
                moves = self.board.get_all_possible_moves(node.player)
                #print("self.board.get_all_possible_moves:", time.time() - bt)
                for move in moves:
                    for eachmove in move:
                        node.child_node.append(TreeNode(eachmove, self.opponent[node.player], node))
            # proceed
            #bt = time.time()
            next = self.mcts_selection(node)
            #print("self.mcts_selection:", time.time() - bt)
            #bt = time.time()
            self.board.make_move(next.move, node.player)
            #print("self.board.make_move", time.time() - bt)
            #bt = time.time()
            result = self.board.is_win(node.player)
            #print("self.board.is_win", time.time() - bt)
            if result:
                if result == self.opponent[node.player]: node.win += 1
                elif result == node.player:
                    next.win += 1
                    next.simulation += 1
                self.board.undo()
                return result
                    #self.board.show_board()
            result = self.mcts(next)
            #bt = time.time()
            self.board.undo()
            #print("self.board.undo()", time.time() - bt)
            # propagate up
            if result == self.opponent[node.player]:
                node.win += 1
            return result
        else:
            bt = time.time()
            result = self.simulate(node.player)
            bt = time.time() - bt
            self.sim_total += bt
            self.sim_counter += 1
            #print("self.simulate", bt)
            node.simulation += 1
            if result == self.opponent[node.player]:
                node.win += 1
            #print("simulating", result)
            return result



    def mcts_selection(self, node): # Select optimal UCB node
        current = node.child_node[0]
        for child in node.child_node:
            #print(current.uct())
            if current.uct() < child.uct():
                current = child
        #print("player", node.player, "pick", current.move)
        return current



    def simulate(self, player):
        win = 0
        counter = 0
        # fake_board = Board(self.col, self.row, self.p)
        # self.copy_board(fake_board)
        #print("DIEN")
        #fake_board.show_board()
        #totaltime = 0
        while win == 0:
            moves = self.board.get_all_possible_moves(player)
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
            self.board.make_move(move, player)
            counter += 1
            #bt = time.time()
            if self.board.tie_counter >= self.board.tie_max:
                win = -1
            #totaltime += time.time() - bt
            #print("self.board.is_win():", time.time() - bt)
            player = self.opponent[player]

        # #print("total time is_win:", totaltime)
        # #bt = time.time()
        for i in range(counter):
            self.board.undo()
        # #rint("total time undo:", time.time() - bt)
        #fake_board.show_board()
        #print("winner", win)
        return win

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

