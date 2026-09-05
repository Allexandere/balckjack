#!/usr/bin/env python3
"""A simple command-line Blackjack game with Hot Streak Bonus.

Rules implemented:
- Single player versus dealer.
- 6-deck shoe, reshuffled when it runs low.
- Blackjack (natural 21) pays 3:2.
- Dealer hits on 16 or less and on soft 17.
- Player actions: hit, stand, double down (first two cards only).
- Aces count as 11 unless that would bust, then as 1.
- NEW: Hot Streak Bonus - Win 3+ hands in a row for bonus chips!
"""

from __future__ import annotations
from streak_bonus import StreakBonus

import random
import sys

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♦", "♣"]  # spades, hearts, diamonds, clubs

STARTING_CHIPS = 100
NUM_DECKS = 6
RESHUFFLE_AT = 52  # cards remaining threshold


class Card:
    __slots__ = ("rank", "suit")

    def __init__(self, rank: str, suit: str) -> None:
        self.rank = rank
        self.suit = suit

    @property
    def value(self) -> int:
        if self.rank in ("J", "Q", "K"):
            return 10
        if self.rank == "A":
            return 11
        return int(self.rank)

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


class Shoe:
    def __init__(self, num_decks: int = NUM_DECKS) -> None:
        self.num_decks = num_decks
        self.cards: list[Card] = []
        self.reshuffle()

    def reshuffle(self) -> None:
        self.cards = [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in SUITS
            for rank in RANKS
        ]
        random.shuffle(self.cards)

    def draw(self) -> Card:
        if len(self.cards) < RESHUFFLE_AT:
            print("\n-- Reshuffling the shoe --")
            self.reshuffle()
        return self.cards.pop()


def hand_value(cards: list[Card]) -> int:
    total = sum(card.value for card in cards)
    aces = sum(1 for card in cards if card.rank == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_soft(cards: list[Card]) -> bool:
    total = sum(card.value for card in cards)
    aces = sum(1 for card in cards if card.rank == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return aces > 0 and total <= 21


def is_blackjack(cards: list[Card]) -> bool:
    return len(cards) == 2 and hand_value(cards) == 21


def show_hands(player: list[Card], dealer: list[Card], hide_dealer: bool = True) -> None:
    if hide_dealer:
        dealer_str = f"{dealer[0]} ??"
        dealer_val = "?"
    else:
        dealer_str = " ".join(str(c) for c in dealer)
        dealer_val = str(hand_value(dealer))
    player_str = " ".join(str(c) for c in player)
    print(f"\n  Dealer: {dealer_str}  (value: {dealer_val})")
    print(f"  You:    {player_str}  (value: {hand_value(player)})")


def prompt_action(can_double: bool) -> str:
    options = "[h]it, [s]tand" + (", [d]ouble down" if can_double else "")
    while True:
        choice = input(f"  Your move ({options}): ").strip().lower()
        if choice in ("h", "hit"):
            return "hit"
        if choice in ("s", "stand"):
            return "stand"
        if can_double and choice in ("d", "double", "double down"):
            return "double"
        print("  Invalid choice, try again.")


def prompt_bet(chips: int) -> int:
    while True:
        raw = input(f"\nYou have {chips} chips. Enter your bet (or 'q' to quit): ").strip().lower()
        if raw in ("q", "quit", "exit"):
            return 0
        try:
            bet = int(raw)
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if bet <= 0:
            print("  Bet must be positive.")
            continue
        if bet > chips:
            print("  You can't bet more than you have.")
            continue
        return bet


def dealer_play(shoe: Shoe, dealer: list[Card]) -> None:
    while True:
        value = hand_value(dealer)
        if value < 17 or (value == 17 and is_soft(dealer)):
            dealer.append(shoe.draw())
        else:
            break


def settle(bet: int, player: list[Card], dealer: list[Card]) -> tuple[int, str]:
    """Return (net chip change, result string) for streak tracking."""
    player_val = hand_value(player)
    dealer_val = hand_value(dealer)
    player_bj = is_blackjack(player)
    dealer_bj = is_blackjack(dealer)

    if player_bj and dealer_bj:
        print("Both have blackjack. Push.")
        return 0, "push"
    if player_bj:
        winnings = int(bet * 3 / 2)
        print(f"Blackjack! You win {winnings} chips.")
        return winnings, "win"
    if dealer_bj:
        print("Dealer has blackjack. You lose.")
        return -bet, "loss"
    if player_val > 21:
        print("You busted. You lose.")
        return -bet, "bust"
    if dealer_val > 21:
        print("Dealer busted. You win!")
        return bet, "win"
    if player_val > dealer_val:
        print("You win!")
        return bet, "win"
    if player_val < dealer_val:
        print("Dealer wins.")
        return -bet, "loss"
    print("Push.")
    return 0, "push"


def play_round(shoe: Shoe, chips: int, streak: StreakBonus) -> int:
    """Play one round with streak tracking."""
    bet = prompt_bet(chips)
    if bet == 0:
        return chips

    player = [shoe.draw(), shoe.draw()]
    dealer = [shoe.draw(), shoe.draw()]

    show_hands(player, dealer, hide_dealer=True)
    
    # Show current streak status
    if streak.current_streak > 0:
        print(f"\n  🔥 Hot Streak: {streak.get_streak_display()}")

    if is_blackjack(player) or is_blackjack(dealer):
        show_hands(player, dealer, hide_dealer=False)
        change, result = settle(bet, player, dealer)
        bonus = streak.update(result)
        if bonus > 0:
            print(f"🎉 STREAK BONUS: +{bonus} chips for {streak.current_streak} wins in a row!")
            change += bonus
        return chips + change

    while True:
        can_double = len(player) == 2 and chips >= bet * 2
        action = prompt_action(can_double)

        if action == "hit":
            player.append(shoe.draw())
            show_hands(player, dealer, hide_dealer=True)
            if hand_value(player) > 21:
                break
        elif action == "double":
            bet *= 2
            player.append(shoe.draw())
            print(f"  Bet doubled to {bet}. You draw one card.")
            show_hands(player, dealer, hide_dealer=True)
            break
        else:  # stand
            break

    if hand_value(player) <= 21:
        dealer_play(shoe, dealer)

    show_hands(player, dealer, hide_dealer=False)
    change, result = settle(bet, player, dealer)
    
    # Update streak and check for bonus
    bonus = streak.update(result)
    if bonus > 0:
        print(f"🎉 STREAK BONUS: +{bonus} chips for {streak.current_streak} wins in a row!")
        change += bonus
    
    return chips + change


def main() -> None:
    print("=" * 40)
    print("        Welcome to Blackjack!")
    print("=" * 40)
    print("Blackjack pays 3:2. Dealer hits soft 17.")
    print("✨ NEW: Hot Streak Bonus - Win 3+ hands in a row for bonus chips!")

    shoe = Shoe()
    chips = STARTING_CHIPS
    streak = StreakBonus()  # Initialize streak tracker

    try:
        while chips > 0:
            chips = play_round(shoe, chips, streak)
            if chips <= 0:
                print("\nYou're out of chips. Game over!")
                break
            
            # Show streak stats after each round
            if streak.current_streak > 0:
                stats = streak.get_stats()
                print(f"\n📊 Streak Stats: {streak.get_streak_display()}")
                print(f"   Longest streak: {stats['longest_streak']}")
                print(f"   Total bonus chips earned: {stats['total_bonus_chips']}")
            
            again = input("\nPlay another round? [Y/n]: ").strip().lower()
            if again in ("n", "no", "q", "quit"):
                break
        
        # Show final streak stats
        stats = streak.get_stats()
        print(f"\n🏆 Final Stats:")
        print(f"   Longest winning streak: {stats['longest_streak']}")
        print(f"   Total bonus chips earned: {stats['total_bonus_chips']}")
        print(f"\nYou leave the table with {chips} chips. Thanks for playing!")
    except (KeyboardInterrupt, EOFError):
        stats = streak.get_stats()
        print(f"\n\nCashing out with {chips} chips. Bye!")
        print(f"🏆 Your best streak was {stats['longest_streak']} wins!")
        sys.exit(0)


if __name__ == "__main__":
    main()