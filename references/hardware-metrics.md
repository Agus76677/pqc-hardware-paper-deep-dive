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

For an isolated operation, integrate power over its measured execution window. Only with matching average power over that entire isolated window:

`energy_J = average_power_W × window_s`

For overlapped steady-state work:

`energy_per_op_J = total_energy_J / completed_operations`

or `average_total_power_W / throughput_ops_s` over the same interval. Do not multiply aggregate pipelined power by individual latency. State total/dynamic power, idle-energy treatment, workload, concurrency and measurement window.

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

Perform independent broader comparison only when the user explicitly requests it. Preserve and explain the original comparison table and verify essential cited claims within the single-paper task; this does not authorize an external ranking.

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


## Persistent definitions and per-row records

The explicit project registry lives at `<output-root>/metrics-registry.json`; each paper receives a snapshot `metrics-registry.json`. Never assume an implicit global registry or recall a previous chat's formula. Register only a user-provided or primary-source-verified definition; no benchmark-paper formulas are preloaded.

Use `hardware_metrics.py register --registry <project-registry> --definition <definition.json>`, then initialize with `prepare_output.py --metrics-registry <project-registry>` or run `hardware_metrics.py compute --paper-dir <paper-dir> --registry <project-registry>`. Compute saves the exact registry snapshot and derived values in the paper directory. A changed formula requires a new version; same ID/version cannot be silently replaced.

Example of an explicitly declared LUT-only convention (an example, not an automatic default or an attributed benchmark formula):

```json
{
  "id": "ATP_LUT_us", "version": "1",
  "formula": "lut * cycles / frequency_MHz", "unit": "LUT*us",
  "required_inputs": {"lut": "LUT", "cycles": "cycles", "frequency_MHz": "MHz"},
  "platform_scope": ["FPGA-Xilinx-7series"],
  "operation_scope": ["NTT256"],
  "resource_weights": {}, "time_definition": "kernel latency from matched cycles and achieved frequency",
  "definition_source": {"user_provided": true, "locator": "User-confirmed LUT-only convention"},
  "verified": true
}
```

Raw results live in `metrics.json`; the same record is one implementation/design point, not a mixture of table rows:

```json
{
  "schema_version": 1,
  "results": [{
    "id": "table3-rowA", "source_id": "paper", "locator": "Table III, row A, paper v2",
    "design_point": "A", "parameter_set": "n=256,q=3329",
    "platform_scope": "FPGA-Xilinx-7series", "operation_scope": "NTT256",
    "device": "exact part", "toolchain": "tool and version",
    "measurement_stage": "post-route", "io_boundary": "kernel only",
    "inputs": {
      "lut": {"value": 18432, "unit": "LUT"},
      "cycles": {"value": 768, "unit": "cycles"},
      "frequency_MHz": {"value": 250, "unit": "MHz"}
    },
    "reported_metrics": [], "notes": "Original table values; no hidden normalization"
  }],
  "derived": []
}
```

Examples must be replaced by actual evidence. Keep every available native resource even if a selected formula does not use it. BRAM18/BRAM36, DSP types, FF/LUT/slice/ALM, kLUT versus LUT, ASIC core versus SRAM inclusion, and time/cycle ATP must have explicit original units and resource granularity. Missing is null/absent, not zero; an explicitly reported zero remains zero. Convert units visibly and preserve original values in notes/additional fields.

The calculator accepts arithmetic expressions over explicitly unit-matched inputs; it does not infer dimensional equivalence or invent conversion weights. platform_scope and operation_scope match explicit lists, and missing/wrong units or incompatible boundaries produce cannot_compute. It records full inputs, formula, definition/version/hash, result locator and unsimplified floating-point value; display rounding must not overwrite raw inputs. Label output `【Analysis】`, keep author reported metrics separately, and manually verify formulas and dimensions before registration.
