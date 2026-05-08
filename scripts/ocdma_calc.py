import math
from scipy.stats import norm

# OCDMA Parameters
Ns = [10000, 50000, 100000]
our_Ks = [105, 230, 322]

print("OCDMA Capacity Analysis (Error-Free Limit)")
for N, K_our in zip(Ns, our_Ks):
    K_bose = int(math.sqrt(N))
    # Error free capacity is exactly K
    U_bose = K_bose
    U_our = K_our
    
    increase = U_our - U_bose
    pct = (increase / U_bose) * 100
    
    print(f"N = {N}:")
    print(f"  Bose K={K_bose} -> Max {U_bose} Users")
    print(f"  Our  K={K_our} -> Max {U_our} Users")
    print(f"  Advantage: +{increase} Users (+{pct:.2f}% network capacity)")

print("\n--- BER Analysis with High Load ---")
# If we allow errors and set U much higher than K (e.g., U = 500 users for N=100000)
# p = K^2 / (2N)
# Gaussian approx BER = Q( sqrt( SIR ) )
# SIR = (2 * N) / ( (U-1) ) ? Actually variance is (U-1)*K^2 / 2N. 
# Signal squared is K^2. SNR = K^2 / ((U-1) * K^2 / 2N) = 2N / (U-1) -> Wait, SNR is independent of K in this simple approx?
# Let's use the combinatorial mean approximation for Probability of Error:
# BER = 1/2 * sum_{i=K}^{U-1} Binom(U-1, i) p^i (1-p)^{U-1-i}

from scipy.special import comb
def calc_ber(N, K, U):
    p = (K**2) / (2 * N)
    if p >= 1: return 1.0
    ber = 0
    # Nota: Questa è un'approssimazione teorica del limite di interferenza (MAI).
    # In un sistema fisico reale, il BER non sarà mai esattamente 0.00 a causa 
    # del rumore termico (Thermal Noise) e del rumore quantico (Shot Noise) dei fotodiodi.
    from scipy.stats import binom
    # P(X >= K) = sf(K-1)
    prob_error = binom.sf(K-1, U-1, p)
    return 0.5 * prob_error

U_heavy = 105
N_test = 10000
K_b = int(math.sqrt(N_test))
K_o = 105

ber_b = calc_ber(N_test, K_b, U_heavy)
ber_o = calc_ber(N_test, K_o, U_heavy)

print(f"For N={N_test}, U={U_heavy} users (Overloaded):")
print(f"  Bose BER: {ber_b:.2e}")
print(f"  Our  BER: {ber_o:.2e}")
if ber_b > 0 and ber_o > 0:
    print(f"  Improvement Factor: {ber_b / ber_o:.1f}x fewer errors")
