# SMRTBuddy — NEBULA X Problem Statement 3

Train condition monitoring across four independent subsystems — Door, ACV, Rail
Corrugation and SHM. Each has its own sensor format, its own task type and its own
disclosed scoring metric, and in service each is monitored by a different system.
SMRTBuddy puts all four behind one interface: pick a subsystem, drop in a data file,
read the result — no code, no per-subsystem tooling.

- **Live app:** `<TBD>`
- **Demo video:** `<TBD>`

> **Status: scaffold.** The directory structure is in place; the models, scoring code
> and dashboard are not yet implemented. Every result and model cell below is
> deliberately blank until produced by a real run. Nothing here is a claimed outcome.

## What it does

Four models over four subsystems, one per subsystem, each trained and scored
independently. A finding is never reported as a bare label. Every one carries three
things:

- **What changed** — the signal and the window that drove the call, so a maintainer
  sees the evidence rather than a verdict.
- **How confident the model is** — reported alongside the prediction, not hidden
  behind a threshold.
- **Which confirmed historical fault it most resembles** — the nearest labelled case
  from that subsystem's training data, so a new finding lands against a fault someone
  has already diagnosed and fixed.

## Results

Scores come from held-out splits, computed with our own implementation of the
disclosed metrics in `scoring/metrics.py` — not from the organisers' held-out set,
which is never released. Subsystem, task and metric are as specified in the PS3 Info
Kits; the score column stays empty until a real run fills it.

| Subsystem | Task | Metric | Our score |
|---|---|---|---|
| Door | Temporal segment detection — find each open/close cycle in the continuous stream, classify Normal / Abnormal resistance | IoU-weighted F1 | |
| ACV | Fault localisation — rank all cars from most to least likely to hold the refrigerant leak | Linear rank-decay score | |
| Rail Corrugation | 3-class classification — Normal / Side I / Side II | Macro F1 | |
| SHM | Regression — cumulative fatigue damage per file | `max(0, 1 − MAPE)` | |

## Model selection

| Subsystem | Approach | Alternatives tried | Why this one |
|---|---|---|---|
| Door | | | |
| ACV | | | |
| Rail Corrugation | | | |
| SHM | | | |

## Explainability

The core mechanism is **nearest-labelled-case retrieval**. Alongside each prediction
the app surfaces the most similar confirmed case from that subsystem's training
labels — the Door segment, ACV case, rail recording or stress file the new input most
closely resembles. A maintainer can then ask the useful question ("is this the same
thing we saw in case 03?") instead of being handed an unexplained score.

**Severity classes are declared domain inputs, not model outputs.** The models predict
only what each subsystem's task defines — a label, a ranking, a damage value. The
severity class attached to a finding is a fixed, human-declared property of the
subsystem, asserted in `scoring/severity.py` and never inferred, learned or varied by a
model. This keeps the operational consequence of a finding traceable to a domain
decision rather than to a model's confidence.

| Severity class | Subsystem(s) |
|---|---|
| Safety-critical | `<TBD>` |
| Safety-relevant | `<TBD>` |
| Availability | `<TBD>` |
| Comfort | `<TBD>` |

## Fit with LTA condition monitoring

The Rail Reliability Taskforce's Annex D condition monitoring baseline names 22 assets
across Trainway, Station and Train Health — doors and air-conditioning among them —
each monitored by a different system, acquired at a different time, from a different
manufacturer. That fragmentation is the practical obstacle: the data exists, but it
arrives in as many formats and interfaces as there are suppliers. This app takes four
such subsystems and presents them through one consistent interface, with the same
interaction and the same shape of output for each.

## Running it

```bash
pip install -r requirements.txt
python scripts/package_submission.py
```

`package_submission.py` is the single entry point that produces the prediction CSVs and
packages them for submission. Both the script and `requirements.txt` are still to be
written — the commands above are the intended interface, not a working pipeline.

## Structure

| Path | Contents |
|---|---|
| `src/` | Per-subsystem model code — `door.py`, `acv.py`, `rail.py`, `shm.py`, over a shared `base.py` interface |
| `scoring/` | Our implementation of the four disclosed metrics (`metrics.py`) and the declared severity mapping (`severity.py`) |
| `scripts/` | Feature extraction and the submission packaging entry point |
| `dashboard/` | The app a non-technical user actually touches |
| `predictions/` | Generated `*_predictions.csv` outputs, the files judges score |

`data/` and `features/` are gitignored — the PS3 datasets are ~6 GB and are not
redistributed here.

## Limitations

These are properties of the provided data, and they bound what any model can claim:

- **Rail Corrugation — 14 Side I training examples.** Against 234 Normal and 24 Side II
  across 272 files. Macro F1 weights that 14-example class equally with the 234-example
  one, so the headline figure is high variance: a handful of Side I calls swings it
  substantially. A single held-out split does not establish a stable score.
- **ACV — 6 labelled cases.** Six training files, one faulty car each, and a single
  distributed test case. That is enough to develop a method against, not enough to
  validate one with any confidence, and the reported score may rest on one file.
- **SHM — no sampling rate, no S-N constants.** The files are single-column raw stress
  series with no header, and neither the sampling frequency nor the S-N curve constants
  (`m`, `C`) are published. Miner's rule cannot be applied analytically, so the damage
  mapping is learned from the 64 training labels rather than computed. The score is also
  MAPE-derived, which weights low-damage files hardest.
- **No held-out organiser labels.** Every score we report is from our own splits. It is
  an estimate of held-out performance, not a measurement of it.
