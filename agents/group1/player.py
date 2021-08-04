from Sequence.sequence_model import COORDS
from template import Agent
import random,heapq
import copy
from Sequence.sequence_utils import *
from queue import Queue
from queue import PriorityQueue

""" heuristic search """

class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)

    def numberOfSequence(self, pos, colour, seq_colour ,oc, os, chips):
        clr, sclr = colour, seq_colour
        seq_type = TRADSEQ
        seq_coords = []
        seq_found = {'vr': 0, 'hz': 0, 'd1': 0, 'd2': 0, 'hb': 0}
        found = False
        nine_chip = lambda x, clr: len(x) == 9 and len(set(x)) == 1 and clr in x
        lr, lc = pos
        chips[lr][lc] == colour

        # All joker spaces become player chips for the purposes of sequence checking.
        for r, c in COORDS['jk']:
            chips[r][c] = clr

        # First, check "heart of the board" (2h, 3h, 4h, 5h). If possessed by one team, the game is over.
        coord_list = [(4, 4), (4, 5), (5, 4), (5, 5)]
        heart_chips = [chips[y][x] for x, y in coord_list]
        if EMPTY not in heart_chips and (clr in heart_chips or sclr in heart_chips) and not (
                oc in heart_chips or os in heart_chips):
            seq_type = HOTBSEQ
            seq_found['hb'] += 2
            seq_coords.append(coord_list)

        # Search vertical, horizontal, and both diagonals.
        vr = [(-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        hz = [(0, -4), (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        d1 = [(-4, -4), (-3, -3), (-2, -2), (-1, -1), (0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        d2 = [(-4, 4), (-3, 3), (-2, 2), (-1, 1), (0, 0), (1, -1), (2, -2), (3, -3), (4, -4)]
        for seq, seq_name in [(vr, 'vr'), (hz, 'hz'), (d1, 'd1'), (d2, 'd2')]:
            coord_list = [(r + lr, c + lc) for r, c in seq]
            coord_list = [i for i in coord_list if 0 <= min(i) and 9 >= max(i)]  # Sequences must stay on the board.
            chip_str = ''.join([chips[r][c] for r, c in coord_list])
            # Check if there exists 4 player chips either side of new chip (counts as forming 2 sequences).
            if nine_chip(chip_str, clr):
                seq_found[seq_name] += 2
                seq_coords.append(coord_list)
            # If this potential sequence doesn't overlap an established sequence, do fast check.
            if sclr not in chip_str:
                sequence_len = 0
                start_idx = 0
                for i in range(len(chip_str)):
                    if chip_str[i] == clr:
                        sequence_len += 1
                    else:
                        start_idx = i + 1
                        sequence_len = 0
                    if sequence_len >= 5:
                        seq_found[seq_name] += 1
                        seq_coords.append(coord_list[start_idx:start_idx + 5])
                        break
            else:  # Check for sequences of 5 player chips, with a max. 1 chip from an existing sequence.
                for pattern in [clr * 5, clr * 4 + sclr, clr * 3 + sclr + clr, clr * 2 + sclr + clr * 2,
                                clr + sclr + clr * 3, sclr + clr * 4]:
                    for start_idx in range(5):
                        if chip_str[start_idx:start_idx + 5] == pattern:
                            seq_found[seq_name] += 1
                            seq_coords.append(coord_list[start_idx:start_idx + 5])
                            found = True
                            break
                    if found:
                        break

        for r, c in COORDS['jk']:
            chips[r][c] = JOKER  # Joker spaces reset after sequence checking.

        num_seq = sum(seq_found.values())
        return num_seq

    def heuristic(self, pos, colour, seq_colour, oc, os, chips):
        x, y = pos


        vr = [(-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        hz = [(0, -4), (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        d1 = [(-4, -4), (-3, -3), (-2, -2), (-1, -1), (0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        d2 = [(-4, 4), (-3, 3), (-2, 2), (-1, 1), (0, 0), (1, -1), (2, -2), (3, -3), (4, -4)]
        maxC = 0
        sequence_count = 0
        for seq in [vr, hz, d1, d2]:
            coord_list = [(r + x, c + y) for r, c in seq]
            coord_list = [i for i in coord_list if 0 <= min(i) and 9 >= max(i)]
            score = 0
            start_idx = 0
            only_one_sequence = True

            for i in range(len(coord_list)):
                x1, y1 = coord_list[i]
                start_idx += 1
                if start_idx > 5:
                    start_idx = 5
                    x2, y2 = coord_list[i - 5]
                    if chips[x2][y2] == seq_colour:
                        score -= 1
                        only_one_sequence = True
                    elif chips[x2][y2] == '#' or chips[x2][y2] == colour:
                        score -= 1
                if chips[x1][y1] == oc or chips[x1][y1] == os:
                    i = i + 4
                    score = 0
                elif chips[x1][y1] == seq_colour and only_one_sequence:
                    score += 1
                    only_one_sequence = False
                elif chips[x1][y1] == '#' or chips[x1][y1] == colour:
                    score += 1

                if score == 4:
                    sequence_count += 1
                maxC = max(maxC, score)

        heart_list = [(4, 4), (4, 5), (5, 4), (5, 5)]
        heart_chips = [chips[y][x] for x, y in heart_list]
        if not (oc in heart_chips or os in heart_chips):
            for heart in heart_list:
                if pos == heart:
                    if maxC < 3:
                        maxC = 3
        return maxC

    def SelectAction(self, actions, game_state):
        id = self.id
        print(f'----------this is in selection of action for agent{id}-----------')

        agent_state = game_state.agents
        board_state = game_state.board

        agent = agent_state[id]
        team_coords = board_state.plr_coords[agent.colour]

        hand_cards = agent.hand
        clr = agent.colour
        sclr = agent.seq_colour
        opr = agent.opp_colour
        osr = agent.opp_seq_colour
        chips = board_state.chips
        currentScore = agent.score

        doubleJ = game_state.board.empty_coords
        singleJ = game_state.board.plr_coords[opr]
        last_act = agent.last_action  # play_card, draft_card, type:'place'or'remove', coords
        # agent_history = agent.agent_trace.action_reward

        draft_cards = board_state.draft
        bestdraft = ''
        maxSc = 0
        for draft in draft_cards:
            if draft == 'jd' or draft == 'jc':
                bestdraft = draft
            elif draft == 'js' or draft == 'jh':
                bestdraft = draft
            else:
                coordlist = COORDS[draft]
                for coord in coordlist:
                    x, y = coord
                    if chips[x][y] == '_':
                        sc = self.heuristic(coord, clr, sclr, opr, osr, chips)
                        if sc > maxSc:
                            bestdraft = draft
                            maxSc = sc

        if actions[0]['type'] == 'trade':
            bestDraft = actions[0]
            bestDscore = 0
            for action in actions:
                draft = action['draft_card']
                if draft == 'jd'or draft== 'jc':
                    return action
                elif draft == 'js' or draft == 'jh':
                    return action
                else:
                    coordlist = COORDS[draft]
                    for coord in coordlist:
                        x,y = coord
                        if chips[x][y] == '_':
                            sc = self.heuristic(coord, clr, sclr, opr, osr, chips)
                            if sc > bestDscore:
                                bestDraft = action
                                bestDscore = sc
            return bestDraft
        else:

            maxScore = 0
            bestCard = actions[0]['play_card']
            bestPos = actions[0]['coords']

            maxremoveScore = 0
            bestRemoveCard = actions[0]['play_card']
            bestRemovePos = actions[0]['coords']
            hand_cards = hand_cards +[bestdraft]
            hasJ = False
            for card in hand_cards:
                if card == 'jc' or card == 'jd':
                    hasJ = True
                    for coord in doubleJ:
                        score = self.heuristic(coord, clr, sclr, opr, osr, chips)
                        if score > maxScore:
                            bestPos = coord
                            bestCard = card
                            maxScore = score
                if card == 'js' or card == 'jh':
                    hasJ = True
                    for coord in singleJ:
                        score = self.heuristic(coord, opr, osr, clr, sclr, chips)
                        if score > maxremoveScore:
                            bestRemovePos = coord
                            bestRemoveCard = card
                            maxremoveScore = score
            if hasJ:
                if maxremoveScore > maxScore:
                    bestCard = bestRemoveCard
                    bestPos = bestRemovePos
                for action in actions:
                    if action['coords'] == bestPos and action['draft_card'] == bestdraft and action['play_card'] == bestCard:
                        return action


            node = ([], 0, hand_cards,0)
            pri = PriorityQueue()
            pri.put((0,node))

            bestCoords = None
            while not pri.empty():
                n = pri.get()
                vcoords, seqnum, thands, minStep = n[1]

                if currentScore + seqnum >= 2:
                    bestCoords = vcoords
                    break
                elif seqnum == 1:
                    bestCoords = vcoords

                for index in range(len(thands)):

                    card = thands[index]
                    for coord in COORDS[card]:
                        x,y = coord
                        if coord not in vcoords and chips[x][y] == EMPTY:
                            tempchips = copy.deepcopy(chips)
                            tempvcoords = vcoords + [coord]
                            for vcoord in vcoords:
                                tempchips[vcoord[0]][vcoord[1]] = clr
                            tempSeqNum= self.numberOfSequence(coord, clr, sclr, opr, osr, tempchips)
                            if len(thands) > 1:
                                #tnode = (tempvcoords, tempSeqNum, thands[1:])
                                #pri.put(tnode)
                                h = 5 - self.heuristic(coord, clr, sclr, opr, osr, tempchips)
                                f = h + len(tempvcoords)
                                tnode = (tempvcoords, tempSeqNum, thands[index+1:], h)
                                pri.put((f, tnode))

            if bestCoords is not None:
                bestscore = 0
                bestaction = actions[0]
                bestcoord = bestCoords[0]
                #for coord in bestCoords:
                    #x, y = coord
                    #for action in actions:
                        #if action['draft_card'] == bestdraft and action['coords'] == coord:
                            #score = self.heuristic(coord, clr, sclr, opr, osr, chips)
                            #if score > bestscore:
                                #bestscore = score
                                #bestaction = action
                for action in actions:
                    if action['draft_card'] == bestdraft and action['coords'] == bestcoord:
                        return action
            else:
                bestcount = 0
                best = actions[0]
                for action in actions:
                    if action['draft_card'] == bestdraft:
                        post = action['coords']
                        count = self.heuristic(post, clr, sclr, opr, osr, chips)
                        if count > bestcount:
                            bestcount = count
                            best = action
                return best
