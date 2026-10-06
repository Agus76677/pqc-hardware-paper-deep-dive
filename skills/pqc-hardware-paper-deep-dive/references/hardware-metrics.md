# Hardware Metrics

Use this reference when a paper reports FPGA or ASIC implementation results.

The purpose is to preserve the paper's original measurements and experimental conditions, then derive a small set of clearly defined metrics when the required inputs are available. It is not a default cross-paper ranking framework.

## Preserve raw results first

For every important implementation result, record the original values before any normalization or recomputation.

Keep, when available:

- algorithm, exact version, parameter set, and security level;
- implemented scope: arithmetic kernel, transform, polynomial multiplication, KeyGen, Encaps/Decaps, Sign/Verify, or complete accelerator;
- platform: FPGA family/device or ASIC technology node;
- toolchain and tool version;
- synthesis, post-synthesis, post-place-and-route, silicon, or board-level measurement stage;
- clock constraint and achieved frequency;
- LUT, FF, DSP, BRAM, URAM, slices, ALMs, SRAM, gate count, area, or other reported resources;
- cycle count;
- latency;
- initiation interval;
- throughput;
- power and energy;
- author-reported ATP, AT²P, throughput/area, energy/op, or other derived metrics;
- the exact formula and unit used by the authors;
- whether I/O, host interface, external memory, preprocessing, software overhead, and communication are included.

Do not replace the paper's original table with normalized values. Preserve both when recomputation is useful.

## Experimental-condition record

Hardware numbers are meaningful only together with their measurement conditions.

For each reported result, retain enough context to answer:

- What exact operation was measured?
- What input/output state defines the transaction boundary?
- Which parameter set and security level were used?
- Which FPGA device or ASIC process was used?
- Which tool and implementation stage produced the result?
- Was timing closed?
- Were DSPs, BRAM/URAM, SRAM, or external memory used?
- Was the result measured, post-route, post-synthesis, or analytically estimated?
- Were I/O and software/host overhead included?
- Was the architecture configured for a specific parallelism level or design point?

Use `未报告` when the paper does not state a required condition.

## Reported metrics versus derived metrics

Separate:

- **Reported** — directly copied from the paper.
- **Recomputed** — derived from reported raw values using an explicit formula.
- **Normalized** — converted to a selected reference definition for comparison.
- **Analysis** — interpretation of what the metric implies.

Never present a recomputed or normalized value as if the authors reported it.

## Basic derived quantities

Use only when the required raw values refer to the same implementation point.

### Latency

When cycle count and frequency correspond to the same design point:

`latency_s = cycles / frequency_Hz`

or equivalently:

`latency_us = cycles / frequency_MHz`

If the paper already reports latency, preserve the reported value and use the recomputation only as a consistency check.

### Throughput

If independent transactions can start every `II_cycles` cycles:

`throughput_ops_s = frequency_Hz / II_cycles`

If only full-operation latency is known and overlap is not demonstrated, do not silently use `1 / latency` as steady-state throughput. Label it explicitly as non-overlapped operation rate when useful.

Do not mix coefficients/s, butterflies/s, NTT/s, polynomial-multiplication/s, KEM/s, signatures/s, or bit/s.

### Energy per operation

When power and latency correspond to the same activity condition:

`energy_J = power_W × latency_s`

Keep estimated power separate from measured power.

## Area-time metrics

There is no universal FPGA area definition.

Always preserve the author's original area model and ATP formula first.

Examples may include:

`ATP = LUT × latency`

`ATP = A_equiv × latency`

`AT²P = area × latency²`

or paper-specific weighted combinations of LUT, DSP, BRAM, FF, slice, ALM, or memory.

Do not compare ATP values from different area definitions as if they shared the same unit.

## Canonical metrics

A project may define one or more canonical metrics for repeated use across papers.

Each canonical metric must specify:

1. exact formula;
2. unit;
3. required raw inputs;
4. resource weights, if any;
5. operation boundary;
6. supported platform scope;
7. provenance of the definition.

Example template:

```text
Metric name:
Reference source:
Platform scope:
Operation scope:
Formula:
Resource weights:
Time definition:
Unit:
Required inputs:
Notes:
```

When the user provides a benchmark-paper formula, register it using this template and apply it automatically only when all required inputs and compatible operation boundaries are available.

If required inputs are missing, report `cannot compute` rather than estimating hidden resources.

## Recommended canonical outputs

For a single-paper deep dive, prefer a small number of transparent derived metrics.

Useful examples include:

- `Latency` from cycles and frequency;
- `LUT × latency` when LUT-only area is intentionally used;
- an explicitly defined equivalent-area ATP when a trusted reference formula is available;
- throughput per LUT or throughput per equivalent area;
- energy per operation when matching power data exists.

Do not proliferate derived metrics merely because they can be calculated.

## FPGA resource discipline

Preserve native FPGA resources separately:

- LUT;
- FF/register;
- DSP;
- BRAM;
- URAM;
- slice/ALM when reported.

Do not invent universal conversion weights among them.

When a canonical equivalent-area formula uses resource weights, identify the source of those weights and keep the unweighted raw resources visible.

Do not treat a design as area-efficient merely because one resource class is small while another resource class is heavily used.

## ASIC discipline

Record, when available:

- technology node;
- standard-cell library;
- supply voltage;
- PVT corner;
- synthesis/place-and-route stage;
- core area;
- gate equivalent;
- SRAM/memory inclusion;
- clock frequency;
- power estimation or measurement method.

Do not normalize across technology nodes unless the normalization model is explicitly defined and requested.

## Timing discipline

Distinguish:

- target frequency;
- achieved frequency;
- reported Fmax;
- post-synthesis timing;
- post-route timing;
- measured operating frequency.

A design that fails timing at a target frequency should not be treated as a valid result at that target frequency.

Do not infer a new Fmax from negative WNS and present it as measured performance unless the paper or tool flow explicitly supports that interpretation.

## Single-paper default

For a normal deep dive of one paper:

1. reproduce the paper's main hardware-results table in a clean form;
2. attach the experimental conditions needed to interpret each result;
3. preserve the author's own derived metrics and formulas;
4. recompute only a few useful metrics;
5. explain which architectural mechanism causes the observed resource/performance behavior.

Do not automatically build a large external comparison table.

## Cross-paper comparison mode

Perform broader comparison only when the user explicitly requests it or when the paper's central claim depends on a small number of clearly identified prior designs.

Before direct comparison, check:

- algorithm/version;
- parameter set;
- security level;
- operation scope;
- platform or technology;
- implementation stage;
- resource accounting;
- timing boundary;
- I/O and software inclusion;
- protection level;
- metric formula.

Classify conclusions as:

- **directly comparable**;
- **conditionally comparable**;
- **not currently comparable**.

Prefer preserving raw values over forcing questionable normalization.

## Interpretation

ATP is a joint area-time cost, not a direct measurement of hardware utilization.

Do not infer PE occupancy, pipeline utilization, memory efficiency, or scheduling quality solely from ATP.

When utilization matters, analyze it separately using evidence such as:

- active versus idle cycles;
- pipeline bubbles;
- memory stalls;
- PE/DSP duty cycle;
- stage imbalance;
- bus or memory-port occupancy;
- resource sharing across algorithm phases.

The most useful conclusion is usually not “metric X is lower”, but why the architecture changed the underlying cost.
