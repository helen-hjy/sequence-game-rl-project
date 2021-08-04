import copy
from queue import Queue
from template import Agent
from Sequence.sequence_model import COORDS

""" BFS """

rSeq = {'rrrrr', 'Xrrrr', 'rXrrr', 'rrXrr', 'rrrXr', 'rrrrX', '#rrrr', 'rrrr#'}
bSeq = {'bbbbb', 'Obbbb', 'bObbb', 'bbObb', 'bbbOb', 'bbbbO', '#bbbb', 'bbbb#'}
midPos = {(4, 4), (4, 5), (5, 4), (5, 5)}


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)

    def validStr(self, chips, pos):
        x, y = pos
        vr = ''
        for i in range(y - 4, y + 5):
            if 0 <= i <= 9:
                vr += chips[x][i]

        hz = ''
        for i in range(x - 4, x + 5):
            if 0 <= i <= 9:
                hz += chips[i][y]

        dd = ''
        for i in range(-4, 5):
            if 0 <= x + i <= 9 and 0 <= y + i <= 9:
                dd += chips[x + i][y + i]

        du = ''
        for i in range(-4, 5):
            if 0 <= x - i <= 9 and 0 <= y + i <= 9:
                du += chips[x - i][y + i]

        return [vr, hz, dd, du]

    def hasSqe(self, chips, pos, color):
        seqNum = 0
        seq = rSeq if color == 'r' else bSeq
        x, y = pos
        chips[x][y] = color
        vr, hz, dd, du = self.validStr(chips, pos)

        for i in range(5, len(vr)+1):
            tempSeq = vr[i-5:i]
            if tempSeq in seq:
                seqNum += 1

        for i in range(5, len(hz)+1):
            tempSeq = hz[i - 5:i]
            if tempSeq in seq:
                seqNum += 1

        for i in range(5, len(dd)+1):
            tempSeq = dd[i - 5:i]
            if tempSeq in seq:
                seqNum += 1

        for i in range(5, len(du)+1):
            tempSeq = du[i - 5:i]
            if tempSeq in seq:
                seqNum += 1

        chips[x][y] = '_'

        score = 0
        for s in [vr, hz, dd, du]:
            for c in s:
                if c == color or c == '#':
                    score += 1

        if pos in midPos:
            score = 30

        return seqNum, score

    def pickDraft(self, chips, hands, drafts, color):

        for card in drafts:
            if card == 'jc' or card == 'jd':
                return card
            elif card == 'js' or card == 'jh':
                return card

        newChips = copy.deepcopy(chips)
        for card in hands:
            coords = COORDS[card]
            for coord in coords:
                newChips[coord[0]][coord[1]] = color

        BestDraft = drafts[0]
        BestSeqNum = -1
        BestScore = 0
        for dcard in drafts:
            coords = COORDS[dcard]
            for coord in coords:
                if newChips[coord[0]][coord[1]] == '_':
                    newChips[coord[0]][coord[1]] = color
                    tempSeqNum, tempScore = self.hasSqe(newChips, coord, color)
                    newChips[coord[0]][coord[1]] = '_'
                    if tempSeqNum > BestSeqNum or (tempSeqNum == BestSeqNum and tempScore > BestScore):
                        BestDraft = dcard
                        BestSeqNum = tempSeqNum
                        BestScore = tempScore

        return BestDraft

    def SelectAction(self, actions, game_state):
        id = self.id
        clr = game_state.agents[id].colour
        oclr = game_state.agents[id].opp_colour

        hands = copy.deepcopy(game_state.agents[id].hand)
        drafts = game_state.board.draft
        chips = game_state.board.chips

        doubleJ = game_state.board.empty_coords
        singleJ = game_state.board.plr_coords[oclr]

        # Find the best draft card
        dcard = self.pickDraft(chips, hands, drafts, clr)

        # If there were a trade state, select the action who has selected draft card.
        if actions[0]['type'] == 'trade':
            for action in actions:
                if action['draft_card'] == dcard:
                    return action

        # Keep this draft in hands
        hands = hands + [dcard]

        # Handle j
        BC = None

        for card in hands:
            if card == 'jc' or card == 'jd':
                BC = doubleJ[0]
                BSN = 0
                BS = 0
                for coord in doubleJ:
                    tempSN, tempS = self.hasSqe(chips, coord, clr)
                    if tempSN > BSN or (tempSN == BSN and tempS > BS):
                        BSN = tempSN
                        BS = tempS
                        BC = coord
                break
            if card == 'js' or card == 'jh':
                BC = doubleJ[0]
                BSN = 0
                BS = 0
                for coord in singleJ:
                    tempSN, tempS = self.hasSqe(chips, coord, clr)
                    tempSN2, tempS2 = self.hasSqe(chips, coord, oclr)
                    if tempSN2 > tempSN or (tempSN == tempSN2 and tempS < tempS2):
                        tempSN = tempSN2
                        tempS = tempS2
                    if tempSN > BSN or (tempSN == BSN and tempS > BS):
                        BSN = tempSN
                        BS = tempS
                        BC = coord
                break

        # if find a J, return it without BFS
        if BC is not None:
            for action in actions:
                if action['coords'] == BC and action['draft_card'] == dcard:
                    return action

        # if there are no J in hands, BFS them
        bfsQueue = Queue()
        node = ([], 0, hands)
        bfsQueue.put(node)

        bestCoords = (-1, -1)
        while not bfsQueue.empty():
            vcoords, seqnum, thands = bfsQueue.get()

            if seqnum >= 2:
                bestCoords = vcoords[0]
                break
            if seqnum == 1:
                bestCoords = vcoords[0]

            card = thands[0]
            for coord in COORDS[card]:
                tempchips = copy.deepcopy(chips)
                tempvcoords = vcoords + [coord]
                for vcoord in vcoords:
                    tempchips[vcoord[0]][vcoord[1]] = clr
                tempSeqNum, tempScore = self.hasSqe(tempchips, coord, clr)
                if len(thands) > 1:
                    tnode = (tempvcoords, tempSeqNum, thands[1:])
                    bfsQueue.put(tnode)

        if bestCoords != (-1, -1):
            for action in actions:
                if action['draft_card'] == dcard and action['coords'] == bestCoords:
                    return action

        fcoords = []
        for card in game_state.agents[id].hand:
            for coord in COORDS[card]:
                fcoords += [coord]

        bestC = actions[0]['coords']
        bestS = 0
        for c in fcoords:
            if chips[c[0]][c[1]] == '_':
                chips[c[0]][c[1]] = clr
                tsn, ts = self.hasSqe(chips, c, clr)
                if ts > bestS:
                    bestS = ts
                    bestC = c
                chips[c[0]][c[1]] = '_'

        for action in actions:
            if action['draft_card'] == dcard and action['coords'] == bestC:
                return action