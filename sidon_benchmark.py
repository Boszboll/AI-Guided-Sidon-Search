import math
import time
import argparse
import sys
from typing import List, Tuple

# ============================================================
# UTILITIES
# ============================================================

def is_prime(n: int) -> bool:
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0: return False
        i += 6
    return True

def factorize(n: int) -> set:
    f = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            f.add(d)
            n //= d
        d += 1
    if n > 1: f.add(n)
    return f

def verify_sidon(s: List[int]) -> bool:
    diffs = set()
    for i in range(len(s)):
        for j in range(i+1, len(s)):
            d = abs(s[j] - s[i])
            if d in diffs: return False
            diffs.add(d)
    return len(set(s)) == len(s)

# ============================================================
# GF(q^3) POLYNOMIAL ARITHMETIC
# ============================================================

def poly_mul_mod(a, b, A, B, C, q):
    prod = [0]*5
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
    return [prod[0]%q, prod[1]%q, prod[2]%q]

def poly_pow(base, exp, A, B, C, q):
    r = [1,0,0]; cur = list(base)
    while exp > 0:
        if exp & 1: r = poly_mul_mod(r, cur, A, B, C, q)
        cur = poly_mul_mod(cur, cur, A, B, C, q); exp >>= 1
    return r

# ============================================================
# SINGER & HALL MULTIPLIERS ENGINE
# ============================================================

def find_best_cut(S: List[int], v: int, N: int) -> Tuple[int, int]:
    """
    Trova la traslazione ciclica ottimale che massimizza il numero di elementi
    all'interno di una finestra di dimensione N.
    """
    max_count = 0
    best_offset = 0
    S_double = S + [x + v for x in S]
    
    left = 0
    for right in range(len(S_double)):
        while S_double[right] - S_double[left] >= N:
            left += 1
        count = right - left + 1
        if count > max_count:
            max_count = count
            best_offset = S_double[left] - 1
            
    return max_count, best_offset

def generate_singer_base(q: int) -> List[int]:
    v = q*q + q + 1
    order = q**3 - 1
    pf = factorize(order)
    
    A_prim, B_prim, C_prim = None, None, None
    for A in range(q):
        for B in range(q):
            for C in range(1, q):
                is_irred = True
                for x in range(q):
                    if (x**3 + A*x**2 + B*x + C) % q == 0:
                        is_irred = False
                        break
                if not is_irred: continue
                if all(poly_pow([0,1,0], order // f, A, B, C, q) != [1,0,0] for f in pf):
                    A_prim, B_prim, C_prim = A, B, C
                    break
            if A_prim is not None: break
        if A_prim is not None: break
    
    if A_prim is None:
        return []
        
    singer = []
    cur = [1, 0, 0]
    alpha = [0, 1, 0]
    for i in range(v):
        if cur[2] == 0: singer.append(i)
        cur = poly_mul_mod(cur, alpha, A_prim, B_prim, C_prim, q)
    return singer

def optimize_multipliers(base_S: List[int], v: int, N: int) -> Tuple[int, int, int, List[int]]:
    max_k_surviving = 0
    best_mult = 1
    best_offset = 0
    best_mult_S = []
    
    for k in range(1, v):
        if math.gcd(k, v) != 1: continue
        mult_S = sorted([(x * k) % v for x in base_S])
        
        count, offset = find_best_cut(mult_S, v, N)
        if count > max_k_surviving:
            max_k_surviving = count
            best_mult = k
            best_offset = offset
            best_mult_S = mult_S
            
    return max_k_surviving, best_mult, best_offset, best_mult_S

def find_maximal_sidon(N: int) -> Tuple[List[int], dict]:
    """
    Ricerca il set di Sidon massimale per un dato N esplorando i Singer Difference Sets 
    e applicando la tecnica dell'Overshooting Modulare combinata con i Moltiplicatori di Hall.
    Esplora domini v fino al 25% più grandi di N per massimizzare l'elasticità topologica.
    """
    print(f"\n[*] Avvio ricerca per N={N}...")
    
    # Calcoliamo i possibili valori primi q. 
    # Puntiamo a domini v (q^2+q+1) che partono da circa N fino a circa 1.25*N.
    start_q = int(math.sqrt(N)) - 1
    if start_q < 2: start_q = 2
    
    q_candidates = []
    q = start_q
    while True:
        if is_prime(q):
            v = q*q + q + 1
            if v >= N * 0.9:  # Partiamo appena sotto N
                q_candidates.append(q)
            if v > N * 1.25:  # Overshoot massimo del 25% (punto di rottura elastica)
                break
        q += 1

    print(f"[*] Primi q da esplorare (Overshooting): {q_candidates}")
    
    global_best_K = 0
    global_best_set = []
    best_meta = {}
    
    t_start = time.time()
    for q in q_candidates:
        v = q*q + q + 1
        print(f"\n  -> Esplorazione q={q} (dominio v={v}, densità teorica={q+1})")
        
        base_S = generate_singer_base(q)
        if not base_S:
            continue
            
        K_surviving, best_mult, best_offset, best_mult_S = optimize_multipliers(base_S, v, N)
        print(f"     Miglior K trovato: {K_surviving} (moltiplicatore k={best_mult}, offset={best_offset})")
        
        if K_surviving > global_best_K:
            global_best_K = K_surviving
            # Costruisci l'array finale
            final_set = sorted([((x - best_offset) % v) or v for x in best_mult_S])
            global_best_set = [x for x in final_set if x <= N]
            best_meta = {
                'q': q,
                'v': v,
                'multiplier': best_mult,
                'offset': best_offset
            }
            
    t_end = time.time()
    print(f"\n[*] Ricerca completata in {t_end - t_start:.2f}s")
    return global_best_set, best_meta

# ============================================================
# MAIN EXECUTABLE
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Generatore SOTA di Insiemi di Sidon Massimali (Hall-Singer Overshooting)")
    parser.add_argument("-n", "--domain", type=int, default=10000, help="Il dominio N per l'insieme (default: 10000)")
    parser.add_argument("-o", "--output", type=str, default="", help="File txt di output (es. sidon.txt)")
    
    args = parser.parse_args()
    N = args.domain
    
    print("=" * 60)
    print("  MAXIMAL SIDON SET DISCOVERY (HALL MULTIPLIER PARADIGM)")
    print("=" * 60)
    
    best_set, meta = find_maximal_sidon(N)
    
    if not best_set:
        print("[!] Nessun set generato.")
        sys.exit(1)
        
    K = len(best_set)
    is_valid = verify_sidon(best_set)
    density = K / math.sqrt(N)
    
    print("\n" + "=" * 60)
    print("[RISULTATO FINALE]")
    print(f" N = {N}")
    print(f" K = {K}")
    print(f" Validazione: {'Superata' if is_valid else 'Fallita'}")
    print(f" Densità: {density:.3f} * sqrt(N)")
    print(f" Geometria: Singer q={meta['q']} (v={meta['v']}) | Moltiplicatore={meta['multiplier']}")
    print("=" * 60)
    
    # Formattazione per stampa e file
    out_lines = []
    out_lines.append(f"# Maximal Sidon Set per N={N}")
    out_lines.append(f"# Cardinalità (K): {K}")
    out_lines.append(f"# Geometria di base: Singer q={meta['q']} (v={meta['v']})")
    out_lines.append(f"# Moltiplicatore di Hall (isomorfismo): k={meta['multiplier']}")
    out_lines.append(f"# Densità: {density:.3f} * sqrt(N)\n")
    
    formatted = [best_set[i:i+10] for i in range(0, len(best_set), 10)]
    for row in formatted:
        out_lines.append("  " + ", ".join(f"{x:5d}" for x in row))
        
    content = "\n".join(out_lines)
    
    print("\nInsieme generato:")
    print(content)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(content)
        print(f"\n[*] Insieme salvato con successo in: {args.output}")
    else:
        # Default save behavior se non specificato
        default_name = f"sidon_N{N}_K{K}.txt"
        with open(default_name, "w") as f:
            f.write(content)
        print(f"\n[*] Insieme salvato di default in: {default_name}")

if __name__ == "__main__":
    main()
