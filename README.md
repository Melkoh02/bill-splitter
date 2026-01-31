# Bill Splitter

A small Python utility to fairly split shared expenses and settle everything into one simple payment per person.

It supports:

* ⏱️ Time-based costs (e.g. hourly pool tables)
* 🍕 Shared tab items
* 💳 Individually paid shared items (automatic reimbursements)
* ⚖️ Fair proportional splits
* 🔁 Single final transaction per participant
* 🧮 Deterministic totals (always sum exactly to the bill)

---

## Setup

### Clone

```bash
git clone https://github.com/Melkoh02/bill-splitter
cd bill-splitter
```

### Create virtual environment

```bash
python -m venv .venv
```

### Activate

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows (PowerShell)**

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

(Currently no external dependencies)

---

## Run

```bash
python settlement_engine.py
```

You’ll get a single list showing how much each participant pays to **X**, with all reimbursements already folded into those totals.

Example output:

```
Sebas  -> X: 136,974
Melkoh -> X: 237,806
Benja  -> X: 140,965
Dave   -> X: 34,781
Kevin  -> X: 45,132
Mathi  -> X: 79,342
```

---

## How it works

1. Split pool costs proportionally by time present
2. Split tab items by participants
3. Convert individually-paid shared items into reimbursements
4. Fold reimbursements into the main settlement
5. Apply rounding drift to a fallback participant
6. Produce one payment per person

---

## Customizing

Edit the inputs inside `settlement_engine.py`:

* participants
* arrival/departure times
* items
* prices
* fallback person

---

## License

MIT

---
