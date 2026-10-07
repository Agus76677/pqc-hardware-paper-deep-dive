# PQC Hardware Domain Checklist

Select only categories that the paper actually covers. Use this checklist to identify the technical dimensions worth extracting, not as a fixed questionnaire.

## Algorithm and implementation scope

- Algorithm family, exact scheme/version, parameter set, security level, and specification status.
- Implemented operation scope: KeyGen, Encaps/Decaps, Sign/Verify, standalone arithmetic kernel, or complete accelerator.
- Mathematical domain, ring/field parameters, coefficient representation, data dimensions, and relevant correctness conditions.
- Algorithm-to-hardware boundary: which operations are implemented in hardware, software, or precomputation.
- Compatibility with the claimed standard or reference algorithm, including any implementation-specific deviations.

## Arithmetic and algorithmic kernels

- Dominant arithmetic kernels and their share of total computation.
- Polynomial/vector/matrix operations, finite-field arithmetic, modular multiplication/reduction, transforms, sampling, hashing, encoding/decoding.
- Mathematical transformation used to reduce operation count, expose parallelism, simplify arithmetic, or improve data locality.
- Operation count, operand width, intermediate range, reduction strategy, precision, and representation.
- Trade-off between arithmetic complexity, control complexity, memory traffic, and hardware cost.

## Lattice-based cryptography

- Polynomial ring structure, matrix-vector multiplication, coefficient domain, and transform-domain representation.
- NTT/INTT structure, radix, butterfly form, CT/GS organization, stage scheduling, scaling, permutation, and twiddle handling.
- Complete versus incomplete transforms and the placement of point-wise multiplication.
- Modular multiplication and reduction: Montgomery, Barrett, specialized reduction, lazy reduction, and implementation-specific variants.
- Sampling, compression/decompression, rounding, decomposition, hint generation, rejection procedures, and SHAKE/Keccak integration when relevant.
- Opportunities for arithmetic, datapath, memory, or control reuse across Kyber/ML-KEM, Dilithium/ML-DSA, Falcon, or related schemes.

## Code-based cryptography

- Code structure, algebraic representation, encoding/decoding method, and dominant computational bottlenecks.
- Binary polynomial arithmetic, sparse/dense representation, cyclic convolution, fixed-weight sampling, and finite-field operations when applicable.
- Decoder architecture, iteration structure, parallelism, memory organization, lookup/computation trade-offs, and failure behavior.
- Relationship between code parameters, decoding complexity, memory footprint, and achievable parallelism.
- Complete-KEM balance among polynomial operations, encoding/decoding, sampling, hashing, and reencryption checks.
- Architectural mechanisms that are specific to code-based schemes versus mechanisms transferable from lattice accelerators.

## Polynomial multiplication and transforms

- Multiplication strategy: schoolbook, Karatsuba, Toom-Cook, NTT, FFT, convolution variants, or hybrid decomposition.
- Decomposition depth, operand partitioning, transform size, and reconstruction procedure.
- Number and type of multipliers, adders, reducers, butterfly units, and reusable processing elements.
- Pipeline organization, stage fusion, stage sharing, and arithmetic reuse.
- Data ordering, permutation, transpose/reordering cost, and interaction with memory banking.
- Whether reduced arithmetic complexity actually translates into reduced latency, area, or ATP at the architecture level.

## Datapath and microarchitecture

- Datapath structure, processing-element organization, pipeline depth, parallelism, and resource sharing.
- Interface between arithmetic units, memories, controllers, and top-level algorithm stages.
- Critical path, fanout, mux depth, routing pressure, and likely timing bottlenecks.
- Scheduling strategy, cycle-level dependencies, pipeline fill/drain behavior, and initiation interval.
- Degree of specialization versus programmability/configurability.
- Relationship between local kernel optimization and full-system performance.

## Memory architecture and data movement

- Register, BRAM/URAM/SRAM/ROM organization, banking, port count, and storage footprint.
- Address generation, buffering, ping-pong organization, conflict avoidance, and intermediate-result storage.
- Data reuse, locality, bandwidth demand, and arithmetic-to-memory balance.
- Twiddle, constant, table, and precomputation storage.
- Cost of data permutation, inter-stage reordering, and format conversion.
- Whether memory or data movement, rather than arithmetic, limits scalability.

## Complete accelerator architecture

- End-to-end flow of KeyGen, Encaps/Decaps, Sign/Verify, or the complete supported protocol.
- Module-level latency and bottleneck distribution across the complete operation.
- Rate matching among arithmetic, sampling, hashing, encoding/decoding, and memory subsystems.
- Module reuse across algorithm phases and its effect on utilization.
- Top-level control, buffering, interfaces, and intermediate data lifetime.
- Difference between kernel-level speedup and actual end-to-end acceleration.

## Unified and multi-algorithm architectures

- Shared arithmetic primitives across algorithms or parameter sets.
- Unified datapaths, configurable reducers, reusable transforms, shared memories, and shared hash units.
- Parameterization of modulus, transform length, coefficient width, and memory layout.
- Reconfiguration and mode-switching overhead.
- Cost of supporting multiple algorithms compared with optimized single-algorithm designs.
- Resource utilization and idle-resource behavior across different workloads.

## Hardware/software co-design

- Hardware/software partition and rationale.
- Processor responsibilities versus accelerator responsibilities.
- Instruction, bus, DMA, cache, or memory-mapped interfaces.
- Data-transfer, synchronization, invocation, and software overhead.
- Kernel latency versus application-level or protocol-level latency.
- Opportunities to change the partition boundary for better utilization or programmability.

## FPGA and ASIC implementation

- FPGA family or ASIC technology node, implementation tools, and reported implementation stage.
- LUT/FF/DSP/BRAM/URAM usage for FPGA designs.
- Area, gate count, frequency, power, and energy for ASIC designs.
- Synthesis-only versus post-place-and-route results.
- Timing constraints, achieved frequency, and whether timing closure is demonstrated.
- Inclusion or exclusion of I/O, host interface, memories, and supporting logic.
- Portability of the architecture across devices, technology nodes, or implementation flows.

## Performance and hardware efficiency

- Cycle count, latency, initiation interval, throughput, and clock frequency.
- Area/resource utilization and how resources are distributed across major modules.
- ATP, AT²P, throughput-per-area, energy-per-operation, or other efficiency metrics used by the paper.
- Exact definition and boundary of every derived metric.
- Relationship between parallelism and resource growth.
- Utilization of multipliers, DSPs, memories, and processing elements across the complete operation.
- Whether the proposed optimization improves arithmetic count, scheduling efficiency, frequency, utilization, memory traffic, or several of these simultaneously.

## Correctness and standard compliance

- Reference model, KAT, test-vector, or software cross-check used for validation.
- Numerical range, modular correctness, truncation, lazy reduction, precision, and overflow conditions.
- Supported parameter sets and corner cases.
- Compliance with the relevant published specification or reference algorithm.
- Any optimization that changes data representation, operation order, sampling behavior, rejection behavior, or numerical approximation.
- Distinction between algorithmic equivalence and implementation-level conformity.

## Implementation security

- Secret-dependent branches, memory accesses, loop counts, and rejection behavior.
- Constant-time properties of arithmetic, sampling, decoding, and control.
- Side-channel countermeasures: masking, hiding, shuffling, balancing, or specialized protected arithmetic.
- Fault-detection or fault-tolerance mechanisms and their architectural overhead.
- Randomness requirements introduced by protection mechanisms.
- Security-performance trade-offs and whether the paper evaluates actual leakage/fault resistance or only discusses it qualitatively.

## Code and RTL correspondence

- Mapping from paper modules and equations to RTL blocks, source files, parameters, FSMs, address generators, memories, and testbenches.
- Top-level hierarchy and major reusable components.
- Configuration mechanism for algorithm, parameter set, or operating mode.
- Build scripts, synthesis constraints, tool versions, and exact code revision.
- Differences between the published architecture and the released implementation.
- Missing modules, undocumented assumptions, or implementation details required for reproduction.

## Prior work and architectural novelty

- Closest prior architecture and the exact mechanism that differs.
- Whether the novelty is mathematical, architectural, memory-centric, scheduling-centric, system-level, or a combination.
- Which bottleneck the proposed mechanism removes or shifts.
- Cost introduced by the improvement: area, routing, control, memory, latency, programmability, or security.
- Whether the claimed contribution is genuinely new or a new combination of known techniques.
- Conditions under which the proposed advantage disappears.

## Research opportunities

- Architectural bottlenecks that remain after the proposed optimization.
- Mechanisms that appear transferable across algorithms, parameter sets, or hardware platforms.
- Opportunities for better arithmetic-memory balance, higher utilization, or more effective resource sharing.
- Potential improvements to ATP, latency, throughput, energy, or configurability.
- Missing ablations or unexplored design-space dimensions.
- Tensions between specialization, reuse, flexibility, and security.
- Hypotheses that can be tested with a minimal RTL prototype, analytical model, synthesis experiment, or controlled architecture comparison.
- Evidence needed to establish a publication-level contribution rather than an incremental implementation optimization.

## Research hypothesis record

A candidate should identify evidence/locator, remaining bottleneck, mechanism to change, closest verified baseline, applicable parameter/platform scope, expected trade-off, minimum experiment, and falsification condition. Separate a testable hypothesis from established novelty; do not attach a personal project, target venue, or fixed benchmark list.
