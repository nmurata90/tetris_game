#!/usr/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime
import pprint
import random
import copy
import numpy as np

class Block_Controller(object):

    # init parameter
    board_backboard = 0
    board_data_width = 0
    board_data_height = 0
    ShapeNone_index = 0
    CurrentShape_class = 0
    NextShape_class = 0

    # GetNextMove is main function.
    # input
    #    nextMove : nextMove structure which is empty.
    #    GameStatus : block/field/judge/debug information. 
    #                 in detail see the internal GameStatus data.
    # output
    #    nextMove : nextMove structure which includes next shape position and the other.
    def GetNextMove(self, nextMove, GameStatus):

        t1 = datetime.now()

        # print GameStatus
        print("=================================================>")
        #pprint.pprint(GameStatus, width = 61, compact = True)

        # get data from GameStatus
        # current shape info
        CurrentShapeDirectionRange = GameStatus["block_info"]["currentShape"]["direction_range"]
        self.CurrentShape_class = GameStatus["block_info"]["currentShape"]["class"]
        # next shape info
        NextShapeDirectionRange = GameStatus["block_info"]["nextShape"]["direction_range"]
        self.NextShape_class = GameStatus["block_info"]["nextShape"]["class"]
        # current board info
        self.board_backboard = GameStatus["field_info"]["backboard"]
        # default board definition
        self.board_data_width = GameStatus["field_info"]["width"]
        self.board_data_height = GameStatus["field_info"]["height"]
        self.ShapeNone_index = GameStatus["debug_info"]["shape_info"]["shapeNone"]["index"]

        # search best nextMove -->
        strategy = None
        LatestEvalValue = -100000
        # search with current block Shape
        for direction0 in CurrentShapeDirectionRange:
            # search with x range
            x0Min, x0Max = self.getSearchXRange(self.CurrentShape_class, direction0)
            for x0 in range(x0Min, x0Max):
                # get board data, as if dropdown block
                board = self.getBoard(self.board_backboard, self.CurrentShape_class, direction0, x0)

                # evaluate board
                #EvalValue = self.calcEvaluationValueSample(board)
                # update best move
                #if EvalValue > LatestEvalValue:
                    #strategy = (direction0, x0, 1, 1)
                    #LatestEvalValue = EvalValue

                # next block
                for direction1 in NextShapeDirectionRange:
                    x1Min, x1Max = self.getSearchXRange(self.NextShape_class, direction1)
                    for x1 in range(x1Min, x1Max):
                        board2 = self.getBoard(board, self.NextShape_class, direction1, x1)
                        EvalValue = self.calcEvaluationValueSample(board2)
                        if EvalValue > LatestEvalValue:
                            strategy = (direction0, x0, 1, 1)
                            LatestEvalValue = EvalValue
        # search best nextMove <--

        print("===", datetime.now() - t1)
        nextMove["strategy"]["direction"] = strategy[0]
        nextMove["strategy"]["x"] = strategy[1]
        nextMove["strategy"]["y_operation"] = strategy[2]
        nextMove["strategy"]["y_moveblocknum"] = strategy[3]
        #print(nextMove)

        return nextMove

    def getSearchXRange(self, Shape_class, direction):
        #
        # get x range from shape direction.
        #
        minX, maxX, _, _ = Shape_class.getBoundingOffsets(direction) # get shape x offsets[minX,maxX] as relative value.
        xMin = -1 * minX
        xMax = self.board_data_width - maxX
        return xMin, xMax

    def getShapeCoordArray(self, Shape_class, direction, x, y):
        #
        # get coordinate array by given shape.
        #
        coordArray = Shape_class.getCoords(direction, x, y) # get array from shape direction, x, y.
        return coordArray

    def getBoard(self, board_backboard, Shape_class, direction, x):
        # 
        # get new board.
        #
        # copy backboard data to make new board.
        # if not, original backboard data will be updated later.
        board = copy.deepcopy(board_backboard)
        _board = self.dropDown(board, Shape_class, direction, x)
        return _board

    def dropDown(self, board, Shape_class, direction, x):
        # 
        # internal function of getBoard.
        # -- drop down the shape on the board.
        # 
        dy = self.board_data_height - 1
        coordArray = self.getShapeCoordArray(Shape_class, direction, x, 0)
        # update dy
        for _x, _y in coordArray:
            _yy = 0
            while _yy + _y < self.board_data_height and (_yy + _y < 0 or board[(_y + _yy) * self.board_data_width + _x] == self.ShapeNone_index):
                _yy += 1
            _yy -= 1
            if _yy < dy:
                dy = _yy
        # get new board
        _board = self.dropDownWithDy(board, Shape_class, direction, x, dy)
        return _board

    def dropDownWithDy(self, board, Shape_class, direction, x, dy):
        #
        # internal function of dropDown.
        #
        _board = board
        coordArray = self.getShapeCoordArray(Shape_class, direction, x, 0)
        for _x, _y in coordArray:
            _board[(_y + dy) * self.board_data_width + _x] = Shape_class.shape
        return _board

    def getWells(self, peaks):
        wells = []

        for i in range(len(peaks)):
            if i == 0:
                w = peaks[1] - peaks[0]
                w = w if w > 0 else 0
                wells.append(w)
            elif i == len(peaks) - 1:
                w = peaks[-2] - peaks[-1]
                w = w if w > 0 else 0
                wells.append(w)
            else:
                w1 = peaks[i - 1] - peaks[i]
                w2 = peaks[i + 1] - peaks[i]
                w1 = w1 if w1 > 0 else 0
                w2 = w2 if w2 > 0 else 0
                w = w1 if w1 >= w2 else w2
                wells.append(w)
        return wells

    def getRowTransitions(self, board):
        sum = 0
        width = self.board_data_width
        height = self.board_data_height
        
        for y in range(height):
            for x in range(1, width):
                if( (board[y * width + x - 1]) != (board[y * width + x]) ):
                    if (board[y * width + x - 1] == self.ShapeNone_index) or (board[y * width + x] == self.ShapeNone_index):
                        sum += 1
        
        return sum

    def getColTransitions(self, board):
        sum = 0
        width = self.board_data_width
        height = self.board_data_height

        for x in range(width):
            for y in range(1, height):
                if( (board[(y - 1) * width + x]) != (board[y * width + x]) ):
                    if (board[(y - 1) * width + x] == self.ShapeNone_index) or (board[y * width + x] == self.ShapeNone_index):
                        sum += 1
        
        return sum
    
    def calcEvaluationValueSample(self, board):
        #
        # sample function of evaluate board.
        #
        width = self.board_data_width
        height = self.board_data_height

        # evaluation paramters
        ## lines to be removed
        fullLines = 0
        ## number of holes or blocks in the line.
        nHoles, nIsolatedBlocks = 0, 0
        ## absolute differencial value of MaxY
        absDy = 0
        ## how blocks are accumlated
        BlockMaxY = [0] * width
        holeCandidates = [0] * width
        holeConfirm = [0] * width

        ### check board
        # each y line
        for y in range(height - 1, 0, -1):
            hasHole = False
            hasBlock = False
            # each x line
            for x in range(width):
                ## check if hole or block..
                if board[y * self.board_data_width + x] == self.ShapeNone_index:
                    # hole
                    hasHole = True
                    holeCandidates[x] += 1  # just candidates in each column..
                else:
                    # block
                    hasBlock = True
                    BlockMaxY[x] = height - y                # update blockMaxY
                    if holeCandidates[x] > 0:
                        holeConfirm[x] += holeCandidates[x]  # update number of holes in target column..
                        holeCandidates[x] = 0                # reset
                    if holeConfirm[x] > 0:
                        nIsolatedBlocks += 1                 # update number of isolated blocks

            if hasBlock == True and hasHole == False:
                # filled with block
                fullLines += 1
            elif hasBlock == True and hasHole == True:
                # do nothing
                pass
            elif hasBlock == False:
                # no block line (and ofcourse no hole)
                pass

        # nHoles
        for x in holeConfirm:
            nHoles += abs(x)

        ### absolute differencial value of MaxY
        BlockMaxDy = []
        for i in range(len(BlockMaxY) - 1):
            val = BlockMaxY[i] - BlockMaxY[i+1]
            BlockMaxDy += [val]
        for x in BlockMaxDy:
            absDy += abs(x)

        # get deepest well
        wells = self.getWells(BlockMaxY)
        max_well = max(wells)

        # number of columns with at least one hole
        n_cols_with_holes = sum(x > 0 for x in holeConfirm)

        # number of columns with zero blocks
        n_pits = sum(x == 0 for x in BlockMaxY)

        # aggregated hight
        agg_height = sum(BlockMaxY)

        # row transitions
        n_row_transitions = self.getRowTransitions(board)

        # col transitions
        n_col_transitions = self.getColTransitions(board)

        # calc Evaluation Value
        # level1 Score : 20418
        score = 0
        score = score + fullLines * 0.376280865005
        score = score + nHoles * -0.961424687169
        score = score + max_well * 0.490560799077
        score = score + n_cols_with_holes * 0.0852372879207
        score = score + absDy * -0.58231177206
        score = score + n_pits * -0.238854198607
        score = score + agg_height * -0.906408053373
        score = score + n_row_transitions * 0.367722108795
        score = score + n_col_transitions * -0.249623252115

        return score

BLOCK_CONTROLLER = Block_Controller()

