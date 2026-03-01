#!/usr/bin/env python3
"""Test signal generator"""
import sys
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/strategies')

from signal_generator import SignalGenerator

print("[TEST] Initializing SignalGenerator...")
sg = SignalGenerator('AAPL', use_model=False)
print("[TEST] SignalGenerator initialized")

print("[DOWNLOAD] Fetching data...")
data = sg.fetch_live_data(lookback_days=250)
if data is not None:
    print(f"[OK] Data fetched: {data.shape}")
    
    print("[SIGNAL] Generating signal...")
    signal = sg.generate_signal(data)
    
    print("\n" + "="*60)
    print(f"SIGNAL: {signal['signal']}")
    print(f"CONFIDENCE: {signal['confidence']:.1%}")
    print(f"REGIME: {signal['regime']}")
    print(f"PRICE: ${signal.get('last_price', 0):.2f}")
    print("="*60)
else:
    print("[ERROR] No data fetched")
