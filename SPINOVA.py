# wheel_app.py - Main Streamlit Application
import streamlit as st
import numpy as np
import hashlib
import secrets
from typing import Dict, List
from datetime import datetime, timedelta

# ========== CORE GAME ENGINE ==========
class WheelGame:
    def __init__(self):
        self.base_weights = {
            0.4: 3, 0.6: 4, 0: 2,
            1.2: 2, 2: 1, 3: 1
        }
        self.jackpot_counter = 0
        self.spin_history = []
        self.user_balances = {'demo_user': 1000.0}
        self.xp_boosts = {}

    def calculate_probabilities(self, user_id: str) -> Dict[float, float]:
        weights = self.base_weights.copy()
        
        # Dynamic difficulty
        if len(self.spin_history) >= 2:
            last_two = [s[1] for s in self.spin_history[-2:]]
            if all(r == 0 for r in last_two):
                weights.pop(0, None)

        # Progressive jackpot
        if self.jackpot_counter >= 100:
            weights[5] = weights.pop(3)

        # Apply XP boosts
        boost = self.xp_boosts.get(user_id, 0)
        if 3 in weights:
            weights[3] += boost
        elif 5 in weights:
            weights[5] += boost

        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}

    def spin_wheel(self, user_id: str, bet: float, client_seed: str) -> dict:
        # Deduct 2% fee
        fee = bet * 0.02
        net_bet = bet - fee
        
        # Provably fair RNG
        server_seed = secrets.token_hex(16)
        combined = f"{server_seed}:{client_seed}"
        hash_digest = hashlib.sha3_256(combined.encode()).hexdigest()
        rand_val = int(hash_digest, 16) % 10000 / 10000

        # Determine result
        probs = self.calculate_probabilities(user_id)
        sorted_sectors = sorted(probs.keys())
        cum_prob = 0
        
        for sector in sorted_sectors:
            cum_prob += probs[sector]
            if rand_val <= cum_prob:
                result = sector
                break

        # Update balances and history
        payout = net_bet * result
        self.user_balances[user_id] += payout
        self.spin_history.append((datetime.now(), result))
        
        # Track jackpot
        if result in (3, 5):
            self.jackpot_counter = 0
        else:
            self.jackpot_counter += 1

        return {
            'result': result,
            'payout': payout,
            'server_seed': server_seed,
            'balance': self.user_balances[user_id]
        }

# ========== STREAMLET UI ==========
def main():
    st.set_page_config(page_title="Crypto Wheel", layout="wide")
    
    if 'game' not in st.session_state:
        st.session_state.game = WheelGame()
    
    # Sidebar Controls
    with st.sidebar:
        st.header("💰 Wallet")
        wallet_address = st.text_input("Connect Wallet")
        
        st.header("🎮 XP System")
        xp = st.number_input("Your XP", 0, 10000, 0)
        if st.button("Boost 3x Chances (+2% for 1h - 35 XP)"):
            handle_xp_boost()
        
    # Main Game Interface
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.title("🎡 Crypto Multiplier Wheel")
        draw_wheel_animation()  # Implement with Plotly/Canvas
        
    with col2:
        st.subheader("Place Bet")
        bet_amount = st.number_input("Bet Amount (USDT)", 1.0, 1000.0, 10.0)
        client_seed = st.text_input("Client Seed", value="your_seed_here")
        
        if st.button("🚀 SPIN!", type="primary"):
            result = st.session_state.game.spin_wheel(
                'demo_user', bet_amount, client_seed
            )
            
            st.metric("Result", f"{result['result']}x")
            st.metric("New Balance", f"${result['balance']:.2f}")
            st.json(result)
            
            if result['result'] == 0:
                if st.button("🔄 Pay 50% for Respin"):
                    handle_respin(bet_amount)
    
    # Leaderboard
    st.subheader("🏆 Daily Leaderboard")
    display_leaderboard()

def draw_wheel_animation():
    # Implement with Plotly/CanvasJS
    st.write("Wheel visualization placeholder")

def handle_xp_boost():
    # Integrate with Stripe/XP system
    st.warning("XP boost feature under development")

def handle_respin(bet_amount: float):
    # Implement respin logic
    st.session_state.game.user_balances['demo_user'] -= bet_amount * 0.5
    st.experimental_rerun()

def display_leaderboard():
    # Connect to database
    st.write("1. Alice - $15,230")
    st.write("2. Bob - $12,450")

if __name__ == "__main__":
    main()

# jackpot.py
import redis

r = redis.Redis()

def update_jackpot():
    current = r.get('jackpot_counter') or 0
    r.set('jackpot_counter', int(current) + 1)

def check_jackpot_ready():
    return int(r.get('jackpot_counter') or 0) >= 100

