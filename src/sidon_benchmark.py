import math
import time
import argparse
import sys
import numpy as np
from numba import njit
from typing import List, Tuple, Dict

# ============================================================
# UTILITIES
# ============================================================

@njit(cache=True)
def is_prime(n: int) -> bool:
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

# Factorize can't return set in numba easily without types, so return a list
@njit(cache=True)
def factorize_list(n: int) -> np.ndarray:
    f = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            f.append(d)
            while n % d == 0:
                n //= d
        d += 1
    if n > 1:
        f.append(n)
    return np.array(f, dtype=np.int64)

def verify_sidon(s: List[int]) -> bool:
    diffs = set()
    for i in range(len(s)):
        for j in range(i+1, len(s)):
            d = abs(s[j] - s[i])
            if d in diffs: return False
            diffs.add(d)
    return len(set(s)) == len(s)

# ============================================================
# GF(q^3) POLYNOMIAL ARITHMETIC (NUMBA ACCELERATED)
# ============================================================

@njit(cache=True)
def poly_mul_mod_njit(a, b, A, B, C, q):
    prod = np.zeros(5, dtype=np.int64)
    for i in range(3):
        for j in range(3):
            prod[i+j] = (prod[i+j] + a[i]*b[j]) % q
    if prod[4]:
        prod[0] = (prod[0] + prod[4]*(A*C)) % q
        prod[1] = (prod[1] + prod[4]*(A*B - C)) % q
        prod[2] = (prod[2] + prod[4]*(A*A - B)) % q
    if prod[3]:
        prod[0] = (prod[0] - prod[3]*C) % q
        prod[1] = (prod[1] - prod[3]*B) % q
        prod[2] = (prod[2] - prod[3]*A) % q
    return np.array([prod[0]%q, prod[1]%q, prod[2]%q], dtype=np.int64)

@njit(cache=True)
def poly_pow_njit(base, exp, A, B, C, q):
    r = np.array([1,0,0], dtype=np.int64)
    cur = base.copy()
    while exp > 0:
        if exp & 1: 
            r = poly_mul_mod_njit(r, cur, A, B, C, q)
        cur = poly_mul_mod_njit(cur, cur, A, B, C, q)
        exp >>= 1
    return r

# ============================================================
# SINGER GENERATION & HALL MULTIPLIERS ENGINE
# ============================================================

@njit(cache=True)
def get_A_B_C(q: int, pf: np.ndarray, order: int):
    for A in range(q):
        for B in range(q):
            for C in range(1, q):
                is_irred = True
                for x in range(q):
                    if (x**3 + A*x**2 + B*x + C) % q == 0:
                        is_irred = False
                        break
                if not is_irred: continue
                
                valid = True
                for f in pf:
                    res = poly_pow_njit(np.array([0,1,0], dtype=np.int64), order // f, A, B, C, q)
                    if res[0]==1 and res[1]==0 and res[2]==0:
                        valid = False
                        break
                if valid:
                    return A, B, C
    return -1, -1, -1

@njit(cache=True)
def build_singer_array(v: int, q: int, A: int, B: int, C: int):
    singer = np.zeros(v, dtype=np.int64)
    count = 0
    cur = np.array([1, 0, 0], dtype=np.int64)
    alpha = np.array([0, 1, 0], dtype=np.int64)
    for i in range(v):
        if cur[2] == 0:
            singer[count] = i
            count += 1
        cur = poly_mul_mod_njit(cur, alpha, A, B, C, q)
    return singer[:count]

def generate_singer_base(q: int) -> np.ndarray:
    v = q*q + q + 1
    order = q**3 - 1
    pf = factorize_list(order)
    
    A, B, C = get_A_B_C(q, pf, order)
    if A == -1:
        return np.array([], dtype=np.int64)
        
    return build_singer_array(v, q, A, B, C)

@njit(cache=True)
def find_best_cut_njit(S: np.ndarray, v: int, N: int):
    max_count = 0
    best_offset = 0
    L = len(S)
    
    S_double = np.zeros(2 * L, dtype=np.int64)
    for i in range(L):
        S_double[i] = S[i]
        S_double[i + L] = S[i] + v
        
    actual_window = N if N < v else v
    left = 0
    for right in range(2 * L):
        while S_double[right] - S_double[left] >= actual_window:
            left += 1
        count = right - left + 1
        if count > max_count:
            max_count = count
            best_offset = S_double[left] - 1
            
    if max_count > L:
        max_count = L
    return max_count, best_offset

@njit(cache=True)
def gcd_njit(a, b):
    while b != 0:
        a, b = b, a % b
    return a

@njit(cache=True)
def optimize_multipliers_njit(base_S: np.ndarray, v: int, N: int):
    max_k_surviving = 0
    best_mult = 1
    best_offset = 0
    
    L = len(base_S)
    best_mult_S = np.zeros(L, dtype=np.int64)
    
    for k in range(1, v):
        if gcd_njit(k, v) != 1: continue
        
        mult_S = np.zeros(L, dtype=np.int64)
        for i in range(L):
            mult_S[i] = (base_S[i] * k) % v
        mult_S.sort()
        
        count, offset = find_best_cut_njit(mult_S, v, N)
        if count > max_k_surviving:
            max_k_surviving = count
            best_mult = k
            best_offset = offset
            for i in range(L):
                best_mult_S[i] = mult_S[i]
            
    return max_k_surviving, best_mult, best_offset, best_mult_S

def find_maximal_sidon(N: int) -> Tuple[List[int], dict]:
    # Partiamo appena sotto N (0.9) fino a overshoot 1.25
    start_q = int(math.sqrt(N)) - 1
    if start_q < 2: start_q = 2
    
    q_candidates = []
    q = start_q
    while True:
        if is_prime(q):
            v = q*q + q + 1
            if v >= N * 0.9:
                q_candidates.append(q)
            if v > N * 1.25:
                break
        q += 1

    global_best_K = 0
    global_best_set = []
    best_meta = {}
    
    # Pre-compile JIT dummy run to avoid timing compilation
    _ = factorize_list(10)
    _ = get_A_B_C(2, np.array([7], dtype=np.int64), 7)
    _ = find_best_cut_njit(np.array([1, 2], dtype=np.int64), 7, 5)
    _ = optimize_multipliers_njit(np.array([1, 2], dtype=np.int64), 7, 5)
    
    for q in q_candidates:
        v = q*q + q + 1
        base_S = generate_singer_base(q)
        if len(base_S) == 0:
            continue
            
        K_surviving, best_mult, best_offset, best_mult_S = optimize_multipliers_njit(base_S, v, N)
        
        if K_surviving > global_best_K:
            global_best_K = K_surviving
            final_set = sorted([int(((x - best_offset) % v) or v) for x in best_mult_S])
            global_best_set = [int(x) for x in final_set if x <= N]
            best_meta = {
                'q': q,
                'v': v,
                'multiplier': int(best_mult),
                'offset': int(best_offset)
            }
            
    return global_best_set, best_meta
