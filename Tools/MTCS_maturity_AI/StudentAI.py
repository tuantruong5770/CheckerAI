from random import randint
from BoardClasses import Move
from BoardClasses import Board
import math
import copy
import time
#The following part should be completed by students.
#Students can modify anything except the class name and exisiting functions and varibles.

C = math.sqrt(2) # Exploration Parameter
NS = 1000
minVisit = 20

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
        for i in range(NS):
            self.mcts(self.current_node)
            #self.board.show_board()
            #print("mcts counter:", i)
        move = self.current_node.child_node[0]
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
                moves = self.board.get_all_possible_moves(node.player)
                for move in moves:
                    for eachmove in move:
                        node.child_node.append(TreeNode(eachmove, self.opponent[node.player], node))
            # proceed
            next = self.mcts_selection(node)
            self.board.make_move(next.move, node.player)
            result = self.board.is_win(node.player)
            if result:
                if result == self.opponent[node.player]: node.win += 1
                elif result == node.player:
                    next.win += 1
                    next.simulation += 1
                self.board.undo()
                return result
                    #self.board.show_board()
            result = self.mcts(next)
            self.board.undo()
            # propagate up
            if result == self.opponent[node.player]:
                node.win += 1
            return result
        else:
            result = self.simulate(node.player)
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
        fake_board = Board(self.col, self.row, self.p)
        self.copy_board(fake_board)
        # print("DIT ME DIEN")
        # fake_board.show_board()
        # totaltime = 0
        while win == 0:
            moves = fake_board.get_all_possible_moves(player)
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
            fake_board.make_move(move, player)
            counter += 1
            # bt = time.time()
            if fake_board.tie_counter >= fake_board.tie_max:
                win = -1
            # totaltime += time.time() - bt
            # print("self.board.is_win():", time.time() - bt)
            player = self.opponent[player]

        # #print("total time is_win:", totaltime)
        # #bt = time.time()
        # for i in range(counter):
        #     self.board.undo()
        # #rint("total time undo:", time.time() - bt)
        # fake_board.show_board()
        return win

    def copy_board(self, board):
        """
        EZ game
        :return: ez board
        """
        board.tie_counter = self.board.tie_counter
        board.tie_max = self.board.tie_max
        board.board = copy.deepcopy(self.board.board)
        board.saved_move = copy.deepcopy(self.board.saved_move)
        board.black_count = self.board.black_count
        board.white_count = self.board.white_count


