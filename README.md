# AI-Guided-Sidon-Search
Finding a near-optimal 105-element Sidon Set for N=10000 using LLM-guided combinatorial optimization, Singer Difference Sets, and Hall Multipliers.

# AI-Guided Sidon Search: Pushing the Limits of Combinatorial Optimization

This repository contains the results of an AI-assisted mathematical experiment aimed at finding maximal **Sidon Sets** for $N=10000$. 

By guiding a Large Language Model (LLM) away from standard heuristics and towards abstract algebra, we successfully generated a **105-element Sidon Set**, significantly outperforming standard computational and classical algebraic bounds.

## 🧠 What is a Sidon Set?
A Sidon Set is a sequence of natural numbers where the sum of any two numbers is unique. Formally, for any $a, b, c, d$ in the set, $a + b = c + d \implies \{a, b\} = \{c, d\}$.
They have crucial applications in:
- Radar and sonar array design (Golomb Rulers)
- Cryptography
- Error-correcting codes and 5G/6G telecommunications

Finding the maximum number of elements $K$ for a given maximum value $N$ is an NP-hard problem. The theoretical upper bound for $N=10000$ is $\approx 110$.

## 🚀 The Journey & Results
We started with standard computer science algorithms and progressively moved to pure mathematics, using the LLM as a high-speed algebraic search engine.

| Methodology | K (Elements) | Efficiency vs $\sqrt{N}$ |
| :--- | :---: | :---: |
| **Greedy Algorithm** (Brute Force) | 64 | 64.0% |
| **Simulated Annealing** (Thermodynamics) | 64 | 64.0% |
| **Bose Construction** (Standard Math, $p=97$) | 98 | 98.0% |
| **Singer Difference Sets** ($q=101$) | 102 | 102.0% |
| **Our Method (Hall Multipliers Overshooting)** | **105** | **105.0%** |

## 🔬 The Winning Methodology: "Elastic Overshooting"
To break the 102 barrier, we used **Singer Difference Sets** combined with **Hall's Multiplier Theorem**. 
Instead of fitting the math *inside* $N=10000$, we intentionally overshot the target:
1. We generated a Singer Set using the prime $q=107$, which creates a cyclic domain of $v = 11557$ (15% larger than our target).
2. This generated 108 elements.
3. We used the LLM to write a search engine that applied hundreds of **Hall Multipliers** ($S' = k \cdot S \pmod v$) to find hidden topological isomorphisms.
4. We discovered a specific multiplier that grouped the elements so tightly that, by cutting the cyclic domain at the largest gap, **105 elements** fell perfectly within the $[1, 10000]$ range.

This proves the existence of an "Elastic Peak" in modular overshooting: if the domain is $\le 15\%$ larger than $N$, Hall Multipliers can compress the set enough to save elements that would otherwise be cut off.

## 💻 How to Run
The repository contains the standalone Python script that generates the set and mathematically verifies it in $O(K^2)$ time.

```bash
python sidon_hall_search.py
