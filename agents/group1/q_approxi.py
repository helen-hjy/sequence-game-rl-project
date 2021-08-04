from Sequence.sequence_utils import *
from Sequence.sequence_model import COORDS, BOARD, SequenceGameRule
from template import Agent
import random, time, copy

rSeq = {'rrrrr', 'Xrrrr', 'rXrrr', 'rrXrr', 'rrrXr', 'rrrrX', '#rrrr', 'rrrr#'}
bSeq = {'bbbbb', 'Obbbb', 'bObbb', 'bbObb', 'bbbOb', 'bbbbO', '#bbbb', 'bbbb#'}
midPos = {(4, 4), (4, 5), (5, 4), (5, 5)}

""" Q-Function Approximation """

DRAFT_NUM = 4
# two-eye jack, one-eye jack, seq_num, chips count
draftWeight = [200, 50, 45, 1]
NUM = 6
# Features: fouhearts, seq_num, chips, opp_seq_num, opp_chips, four corners
placeWeight = [5, 100, 2, 50, 1, 10]
removeWeight = [10, 50, 1, 2, 2, 8]
E = 0.1
GAMMA = 0.9
ALPHA = 0.0005


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

    # check sequence for returning number of sequence and chips number
    def hasSqe(self, chips, pos, color,scolor):
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

        count = 0
        for heart in midPos:
            xh,yh = heart
            if chips[xh][yh] == color or chips[xh][yh] == scolor:
                count += 1
        if count == 4:
            seqNum += 2
        chips[x][y] = '_'

        score = 0
        for s in [vr, hz, dd, du]:
            for c in s:
                if c == color or c == '#':
                    score += 1

        return seqNum, score


    # calculate draft feature value by getting max sequence number and chip number on board
    def draftFeatureValue(self, card, chips, clr,sclr):
        value = [0, 0, 0, 0]
        # one-eye jack in index 2, two-eye in index 1. boolean value checking if they exist
        if card == 'js' or card == 'jh':
            value[0] = 1
            return (value)
        if card == 'jc' or card == 'jd':
            value[1] = 1
            return (value)

        positions = COORDS[card]

        for x, y in positions:
            if chips[x][y] == EMPTY:
                # assign as my team's colour
                copy_chips =  copy.deepcopy(chips)
                copy_chips[x][y] = clr
                # find the seq_num and chips_count
                seqNum, score = self.hasSqe(copy_chips,(x,y),clr,sclr)
                # return max value into list
                value[2] = max(value[2], seqNum)
                value[3] = max(value[3], score)

        return value

    # calculate feature values by checking hearts(bool), sequences and chips count
    def getFeatureValue(self, coord, chips, clr, sclr, opr, osr):

        value = [0, 0, 0, 0, 0, 0]
        if coord in midPos:
            value[0] = 1
        x, y = coord
        chips[x][y] = clr  # assign our colour to chips
        if (x, y) == (0, 0) or (x, y) == (0, 9) or (x, y) == (9, 9) or (x, y) == (9, 0):
            value[5] = 1
        # get seq_num, chips_count of our team
        value[1], value[2] = self.hasSqe(chips, (x, y), clr,sclr)
        chips[x][y] = opr  # assign oppo colour to chips
        # get seq_num, chips_count of oppo team
        value[3], value[4] = self.hasSqe(chips, (x, y), opr,osr)
        chips[x][y] = EMPTY  # reset chip

        return value

    # calcualte linear Q value
    def Qvalue(self, f, w):
        q = 0
        for i in range(len(f)):
            q += f[i] * w[i]
        return q

    def SelectAction(self, actions, game_state):
        id = self.id

        print(f'----------this is in selection of action for agent{id}-----------')
        id = self.id
        agent_state = game_state.agents
        board_state = game_state.board

        agent = agent_state[id]
        team_coords = board_state.plr_coords[agent.colour]

        hand_cards = agent.hand
        draft_cards = board_state.draft
        clr = agent.colour
        sclr = agent.seq_colour
        opr = agent.opp_colour
        osr = agent.opp_seq_colour
        chips = board_state.chips
        first_act = actions[0]  # initial action


        # deep copy chips board
        chipsCopy = copy.deepcopy(chips)


        # find best draft card
        maxQ = 0
        bestDraft = draft_cards[0]
        for card in draft_cards:
            draftFeature = self.draftFeatureValue(card, chipsCopy, clr, sclr)
            currentQ = self.Qvalue(draftFeature, draftWeight)
            if currentQ > maxQ:
                maxQ = currentQ
                bestDraft = card

        # if first action is trade, return best draft card to trade
        if first_act['type'] == 'trade':
            for act in actions:
                if act['draft_card'] == bestDraft:
                    return act
        # if first action is place or remove
        else:
            # calculate Q-value for different features
            bestAction = []
            maxQ = 0
            for act in actions:
                if act['draft_card'] == bestDraft:
                    # find best remove card
                    if act['type'] == 'remove':
                        if maxQ == 0:
                            bestAction = act
                        fv = self.getFeatureValue(act['coords'], chips, clr, sclr, opr, osr)
                        qValue = self.Qvalue(fv, removeWeight)
                    # find best place card
                    if act['type'] == 'place':
                        fv = self.getFeatureValue(act['coords'], chips, clr, sclr, opr, osr)
                        qValue = self.Qvalue(fv, placeWeight)
                    # assign maxQ
                    if qValue > maxQ:
                        maxQ = qValue
                        bestAction = act
        return bestAction
