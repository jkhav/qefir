# qefir

**Q**uantum **E**volutionary **F**ramework for **I**terative **R**efinement: genetic search for quantum circuits
(repeat-until-success circuits first). A population of gate-list genomes evolves by selection (tournament,
stochastic universal sampling), one-point or uniform crossover, and mutation; fitness comes from simulating the
circuits with DDSIM or SliQSim. Companion to [milq](https://github.com/QuantumFIT/milq) (exact SAT synthesis) and
[cheese](https://github.com/jkhav/cheese) (exact GPU search).

Setup: `source setup_env.sh` (updates the SliQSim submodule, builds it, activates `.venv`). Code in `src/`,
tests in `tests/`, reference RUS circuits in `reference_rus_circuits/`.
