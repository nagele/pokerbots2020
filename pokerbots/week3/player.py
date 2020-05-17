'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
import eval7
import random
from numpy.random import geometric

class Player(Bot):
    '''
    A pokerbot.
    '''
    def permute_values(self):
        '''
        Selects a value permutation for the whole game according the prior distribution.
        '''
        orig_perm = list(range(13))[::-1]
        prop_perm = []
        seed = geometric(p=0.25, size=13) - 1
        for s in seed:
            pop_i = len(orig_perm) - 1 - (s % len(orig_perm))
            prop_perm.append(orig_perm.pop(pop_i))
        return prop_perm

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        #nothing in here counts towards 30 seconds
        self.VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.SUITS = list('cdhs')
        self.wins_dict = {v : 1 for v in self.VALUES}
        self.showdowns_dict = {v : 2 for v in self.VALUES}
        self.proposal_perms = []
        for j in range(1000): #play around wiht number
            proposal_perm = self.permute_values() #list with entries [0,12]
            perm_dict = {}
            for i, v in enumerate(self.VALUES):
                for s in self.SUITS:
                    card = v+s
                    permuted_i = proposal_perm[i]
                    permuted_v = self.VALUES[permuted_i]
                    permuted_card = eval7.Card(permuted_v+s)
                    perm_dict[card] = permuted_card
            self.proposal_perms.append(perm_dict)
        perm_mistakes = {} #narrow down to best perms; instead of weeding further, track the nums that they get wrong

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        #round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[active]  # your cards
        #big_blind = bool(active)  # True if you are the big blind

        #not all permutations are equally likely
        #generate a permutation and check if its consistent with showdown results
        #P(M|S)=P(S|M)P(M)/P(S)
        # P(M|S) is posterior probability
        #   P(M) prior distribution (engine's sampling process)
        #   bypass P(S) by using number of samples

        #1. replace cards with current permuation guess
        #2. evaluate hands
        #3. if not consistent, this cant be correct permuation
        pass

    def find_winning_hand(self, winners_hand, deck):
        '''
        returns the hand with highest evaluation score
        '''
        max_score = 0
        max_hand = []
        hand = [eval7.Card(winners_hand[0]), eval7.Card(winners_hand[1])]
        for card1 in deck:
            hand.append(eval7.Card(card1))
            for card2 in deck:
                if card2!=card1:
                    hand.append(eval7.Card(card2))
                    for card3 in deck:
                        if card3!=card1 and card3!=card2:
                            hand.append(eval7.Card(card3))
                            score = eval7.evaluate(hand)
                            if score>max_score:
                                max_score = score
                                max_hand = hand
                            hand.remove(eval7.Card(card3))
                    hand.remove(eval7.Card(card2))
            hand.remove(eval7.Card(card1))
        final_hand = []
        suit_dict = {0:"c", 1: "d", 2:"h", 3: "s"}
        for card in max_hand:
            c = str(card.rank+2)+suit_dict[card.suit]
            if c not in winners_hand:
                if card.rank>=8:
                    if str(card.rank)=="8":
                        c = "T"+suit_dict[card.suit]
                    elif str(card.rank)=="9":
                        c = "J"+suit_dict[card.suit]
                    elif str(card.rank)=="10":
                        c = "Q"+suit_dict[card.suit]
                    elif str(card.rank)=="11":
                        c = "K"+suit_dict[card.suit]
                    elif str(card.rank)=="12":
                        c = "A"+suit_dict[card.suit]
                final_hand.append(c)
        return final_hand  

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        board_cards = previous_state.deck[:street]
        new_perms = []
        if opp_cards!=[]: #showdown
            #eliminate all inconsistent permuations
            for perm in self.proposal_perms:
                my_perm_cards = [perm[c] for c in my_cards]
                opp_perm_cards = [perm[c] for c in opp_cards]
                board_perm_cards = [perm[c] for c in board_cards]
                my_Cards_available = my_perm_cards+board_perm_cards
                opp_cards_available = opp_perm_cards+board_perm_cards
                #did we win showdown
                my_strength = eval7.evaluate(my_Cards_available)
                opp_strength = eval7.evaluate(opp_cards_available)
                #can be consistent with my win
                if my_strength>opp_strength and my_delta>0:
                    new_perms.append(perm)
                #consistent with opp win
                if my_strength<opp_strength and my_delta<0:
                    new_perms.append(perm)
                if my_strength==opp_strength and my_delta==0:
                    new_perms.append(perm)
            self.proposal_perms = new_perms if len(new_perms)>0 else self.proposal_perms
        if opp_cards != []:
            deck = previous_state.deck
            if my_delta > 0:  # we won
                self.wins_dict[my_cards[0][0]] += 1
                self.wins_dict[my_cards[1][0]] += 1
                winning_hand = self.find_winning_hand(my_cards, deck)
                for card in winning_hand:
                    self.wins_dict[card[0]] +=1
                    self.showdowns_dict[card[0]] += 1
        #dont play low pairs
        #can compare pairs, depending on who won, to deduce which is higher
            self.showdowns_dict[my_cards[0][0]] += 1
            self.showdowns_dict[my_cards[1][0]] += 1
            if my_delta < 0:  # we lost
                self.wins_dict[opp_cards[0][0]] += 1
                self.wins_dict[opp_cards[1][0]] += 1
                winning_hand = self.find_winning_hand(opp_cards, deck)
                for card in winning_hand:
                    self.wins_dict[card[0]] +=1
                    self.showdowns_dict[card[0]] += 1
            self.showdowns_dict[opp_cards[0][0]] += 1
            self.showdowns_dict[opp_cards[1][0]] += 1

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, river, or turn respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        pot_after_continue = my_contribution+opp_contribution+continue_cost
      
        if RaiseAction in legal_actions:
           min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
           min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
           max_cost = max_raise - my_pip  # the cost of a maximum bet/raise
           first_card_winrate = self.wins_dict[my_cards[0][0]] / self.showdowns_dict[my_cards[0][0]]
           second_card_winrate = self.wins_dict[my_cards[1][0]] / self.showdowns_dict[my_cards[1][0]]
           winrates = [first_card_winrate, second_card_winrate]
           #how often board cards match pocket cards
           agree_counts = [0,0]
           raise_amount = my_pip + continue_cost + int(0.77 * pot_after_continue)
           raise_amount = min(raise_amount, max_raise)
           raise_amount = max(raise_amount, min_raise)
           if len(self.proposal_perms) <= 5:
            royal_flush = 135004160
            straight_flush = 134610944
            low_pair = 16820320
            high_pair = 34342912
            highest_card = 829538
            #print(eval7.evaluate([eval7.Card("Ad"), eval7.Card("7h"), eval7.Card("2c"), eval7.Card("Ah"),eval7.Card("Td"),eval7.Card("2h"),eval7.Card("5c")]))
            if round_state.street==5:
                #permute the hand and bet according to the scores
                running_score = 0
                for perm in self.proposal_perms:
                    hand = [perm[i] for i in board_cards]
                    my_perm_cards = [perm[c] for c in my_cards]
                    hand.extend(my_perm_cards)
                    score = eval7.evaluate(hand)
                    running_score+=score
                    # if score==royal_flush or score>=straight_flush:
                    #     return RaiseAction(max_raise)
                running_score = running_score/len(self.proposal_perms)
                if running_score<low_pair: #random.randrange(highest_card,royal_flush):
                    if FoldAction in legal_actions:
                        return FoldAction()
                elif running_score>=high_pair:
                    if RaiseAction in legal_actions:
                        return RaiseAction(raise_amount)
           else:
               for card in board_cards:
                for i in range(2):
                    if my_cards[i][0]==card[0]:
                        agree_counts[i]+=1
               #two pair or better
               if sum(agree_counts)>=2:
               #definitely raise
                return RaiseAction(raise_amount)
               #one pair in first card
               if agree_counts[0]==1:
                if random.random()<winrates[0]:
                    return RaiseAction(raise_amount)
               #one pair in seond card
               if agree_counts[1]==1:
                if random.random()<winrates[1]:
                    return RaiseAction(raise_amount)
               #high pocket pairs are extremely good
               if my_cards[0][0]==my_cards[1][0]: #pocket pair
                if random.random() < winrates[0]:
                    return RaiseAction(raise_amount)
               if first_card_winrate > 0.5 and second_card_winrate > 0.5:
                    return RaiseAction(raise_amount)

        if CheckAction in legal_actions:  # check-call
            return CheckAction()
        return CallAction()


if __name__ == '__main__':
    run_bot(Player(), parse_args())
