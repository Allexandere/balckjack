#!/usr/bin/env python3
"""Hot Streak Bonus Module - Tracks winning streaks and rewards players.

When a player wins 3 hands in a row, they get a bonus chip reward.
The bonus increases with longer streaks!

Bonus structure:
- 3 wins in a row: +5 bonus chips
- 5 wins in a row: +10 bonus chips  
- 7 wins in a row: +20 bonus chips
- 10+ wins in a row: +50 bonus chips
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StreakBonus:
    """Tracks player's winning streak and calculates bonuses."""
    
    current_streak: int = 0
    longest_streak: int = 0
    total_bonus_chips: int = 0
    last_result: Optional[str] = None
    
    # Bonus thresholds: (wins_required, bonus_amount)
    BONUS_TABLE = [
        (3, 5),    # 3 wins = 5 bonus chips
        (5, 10),   # 5 wins = 10 bonus chips
        (7, 20),   # 7 wins = 20 bonus chips
        (10, 50),  # 10 wins = 50 bonus chips
    ]
    
    def update(self, result: str) -> int:
        """
        Update streak based on round result.
        
        Args:
            result: 'win', 'loss', or 'push'
        
        Returns:
            Bonus chips awarded (0 if no bonus)
        """
        if result == "win":
            self.current_streak += 1
            self.longest_streak = max(self.longest_streak, self.current_streak)
            bonus = self._check_bonus()
            if bonus > 0:
                self.total_bonus_chips += bonus
                self.last_result = result
                return bonus
        elif result in ("loss", "bust"):
            self.current_streak = 0
        elif result == "push":
            # Push doesn't affect streak (neither win nor loss)
            pass
        
        self.last_result = result
        return 0
    
    def _check_bonus(self) -> int:
        """Check if current streak qualifies for a bonus."""
        for wins, bonus in self.BONUS_TABLE:
            if self.current_streak == wins:
                return bonus
        # Additional bonus for streaks beyond 10
        if self.current_streak > 10:
            return 50 + ((self.current_streak - 10) * 5)  # +5 per extra win
        return 0
    
    def reset(self) -> None:
        """Reset streak (called when player cashes out)."""
        self.current_streak = 0
    
    def get_streak_display(self) -> str:
        """Get a visual representation of the current streak."""
        if self.current_streak == 0:
            return "No current streak"
        
        emojis = "🔥" * min(self.current_streak, 5)
        emojis += "✨" * (self.current_streak - 5) if self.current_streak > 5 else ""
        
        return f"{emojis} {self.current_streak} wins in a row!"
    
    def get_stats(self) -> dict:
        """Get streak statistics."""
        return {
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "total_bonus_chips": self.total_bonus_chips,
        }