# Adaptive Article Structure

Use this fixed main structure. Add, remove, or rename lower-level subsections to match the paper type and the actual technical contribution. Keep the article centered on the paper's evidence rather than forcing every hardware topic into every paper.

## Fixed main sections

1. **论文概述**: problem, motivation, cryptographic target, implementation scope, principal contribution, key result, applicability.
2. **背景与相关工作**: only the algorithmic, architectural, and implementation context needed to understand the claimed difference.
3. **问题定义**: inputs, outputs, notation, parameter set, computation scope, assumptions, target platform, optimization objective, evaluation setting.
4. **方法**: algorithm-to-hardware mapping, architecture, modules, arithmetic, memory organization, scheduling, formulas, implementation flow, and code/RTL mapping when available.
5. **实验**: platform, synthesis/implementation conditions, correctness evidence, resource utilization, frequency, cycle count, latency, throughput, energy/power when reported, ablations, and comparison with prior work.
6. **方法分析**: why it works, actual novelty, bottleneck addressed, architectural trade-offs, essential differences from prior work, and key assumptions.
7. **局限性**: author-stated limitations and separately labeled analysis, including implementation scope, parameter coverage, portability, measurement boundaries, reproducibility, and security caveats when relevant.
8. **启发与研究思考**: evidence-grounded architectural insights, transferable mechanisms, follow-up hypotheses, and experiments that could validate or falsify them.
9. **资料来源**: explain provenance policy; keep detailed records in `sources.yaml` and BibTeX.

## Add subsections by paper type

- **PQC algorithm implementation**: standardized algorithm/version, parameter sets, primitive decomposition, operation counts, critical kernels, data dependencies, implementation scope, and deviations from the reference specification.
- **Polynomial arithmetic**: ring/field definition, polynomial representation, multiplication strategy, NTT/INTT, schoolbook/Karatsuba/Toom-Cook or other decomposition, modular reduction, coefficient width, and reuse across parameter sets.
- **Modular arithmetic**: modulus properties, multiplication/reduction method, datapath width, DSP/LUT mapping, pipelining, operand reuse, and arithmetic correctness.
- **Sampling and encoding**: sampler type, randomness source assumptions, rejection behavior, encoding/decoding, compression/decompression, memory traffic, and constant-time implications.
- **Hashing and symmetric primitives**: SHA-2/SHA-3/SHAKE/AES integration, standalone versus shared cores, interface width, scheduling, buffering, and interaction with the main datapath.
- **Memory architecture**: BRAM/URAM/register organization, banking, port requirements, buffering, address generation, data reuse, memory footprint, bandwidth, and conflicts between computation and storage.
- **Microarchitecture**: processing elements, datapath organization, parallelism, pipeline stages, initiation interval, resource sharing, scheduling, control FSM, and module interfaces.
- **Complete accelerator**: end-to-end operation flow, key generation/encapsulation/decapsulation or sign/verify sequencing, module reuse, host interface, internal communication, and system-level bottlenecks.
- **Multi-algorithm or unified architecture**: common arithmetic structures, shared datapaths, configurable modules, algorithm-specific exceptions, reconfiguration overhead, and the cost of generality.
- **FPGA implementation**: device family, synthesis/place-and-route tool and version, clock constraints, LUT/FF/DSP/BRAM/URAM usage, achieved frequency, timing closure, I/O inclusion, and implementation-stage versus synthesis-only results.
- **ASIC implementation**: technology node, standard-cell library, synthesis/place-and-route conditions, area, frequency, power, energy, gate-equivalent metrics, and assumptions behind cross-node comparisons.
- **Performance optimization**: latency decomposition, cycle count, throughput, initiation interval, concurrency, critical path, area-time or area-time² metrics, and the causal link between the proposed mechanism and the measured improvement.
- **Hardware/software co-design**: partition boundary, processor/accelerator responsibilities, communication overhead, instruction or API interface, DMA/data movement, and whether reported latency includes software and transfer costs.
- **Side-channel or implementation security**: threat model, constant-time behavior, secret-dependent control/data access, masking/hiding/countermeasures, randomness requirements, leakage evaluation, and security-performance trade-offs.
- **Fault resistance**: fault model, detection/correction mechanism, redundancy, coverage, injected-fault methodology, and area/latency overhead.
- **Standard compliance**: exact specification or standard revision, required parameter sets, mandatory algorithmic behavior, implementation deviations, and whether an optimization changes assumptions relevant to correctness or security.

## Section ownership

Keep one authoritative location for every technical detail.

**背景与相关工作** explains only the prerequisite algorithmic and architectural context needed to understand the paper's contribution; it should not become a general textbook on PQC, RTL, or FPGA design.

**问题定义** owns the exact cryptographic operation, parameter set, input/output semantics, implementation boundary, assumptions, target platform, and optimization objective.

**方法** owns the end-to-end algorithm-to-hardware mapping. Architecture explains the global dataflow; arithmetic subsections define computation; memory subsections explain storage and movement; scheduling subsections explain cycle-level execution and resource reuse. Do not duplicate the same mechanism across these subsections.

**实验** owns measured or reported evidence. Resource utilization, frequency, cycle count, latency, throughput, power, and derived efficiency metrics belong here together with the conditions under which they were obtained. Clearly distinguish reported values from independently recomputed values.

**方法分析** connects architectural choices to observed results. It should explain the causal chain from bottleneck to mechanism to hardware effect, identify what is genuinely new relative to the closest prior work, and expose the cost of the optimization.

**局限性** owns unsupported parameter sets, incomplete operation coverage, synthesis-only evidence, omitted I/O or communication costs, portability assumptions, missing reproducibility evidence, and security boundaries that materially affect interpretation.

**启发与研究思考** should not repeat the paper's future-work paragraph. Convert evidence from the paper into concrete research hypotheses, minimal experiments, baselines, ablations, and falsification conditions.

## Evidence discipline

Separate the following whenever they are materially different:

- **Author claim** — what the paper explicitly states.
- **Reported result** — a number, table, figure, formula, or implementation fact directly supported by the paper or artifact.
- **Code/RTL evidence** — behavior or structure verified from the released implementation.
- **Specification evidence** — requirements or algorithm definitions verified against the relevant standard or reference specification.
- **Analysis** — conclusions inferred from the above evidence.

Do not silently upgrade an inference into a paper fact.

## Scope discipline

A local optimization paper does not need a fabricated full-system architecture. Analyze the optimized kernel deeply and state the boundary of its system-level impact.

A full accelerator paper should connect primitive arithmetic, memory organization, scheduling, and top-level protocol flow rather than treating them as isolated modules.

A security-focused implementation paper should expand the relevant threat model and countermeasure analysis rather than forcing an equally detailed performance-optimization narrative.

A paper without released RTL or source code should not receive invented code mapping. State explicitly which implementation details are unavailable.
