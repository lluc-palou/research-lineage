# BTC Directional Classifier via LSTM and Focal Loss

## Theoretical Scope
- Sequence modeling (LSTM)
- Imbalanced classification (focal loss)
- Financial time series feature engineering

## Goal
Predicting short-horizon directional price movements in Bitcoin from 5-minute OHLCV
data is complicated by the near-random nature of the signal and severe class imbalance
between neutral and directional labels. A reliable classifier with statistically
significant edge on the UP class would serve as the signal layer of an automated
trading system.

## Proposed Solution
An LSTM classifier is trained on a sliding window of engineered features extracted
from 5-minute BTC/USDT candles, with focal loss replacing cross-entropy to suppress
the dominant neutral class and concentrate gradient signal on the minority directional
labels. Three output classes (UP, DOWN, NEUTRAL) are defined by a symmetric threshold
applied to forward returns.

## Concepts

### LSTM {#C1}
A recurrent architecture that maintains a gated hidden state across sequential inputs,
making it suitable for capturing temporal dependencies in financial time series.
In this system it processes fixed-length windows of feature vectors and produces
a softmax distribution over the three directional classes.

### Focal Loss {#C2}
A modification of cross-entropy that down-weights well-classified examples via a
modulating factor applied to the standard log-probability term, concentrating learning
on hard or rare examples. Here it suppresses the NEUTRAL majority class and forces
the model to extract discriminative signal from the minority UP and DOWN labels.

## Implementation

### Feature Pipeline {#I1}
Sliding-window extraction over 5-minute OHLCV candles, producing fixed-length feature
vectors per timestep (returns, volatility, volume ratios). Window length and stride
are configured per experiment.

### Training Loop {#I2}
PyTorch training loop with the LSTM classifier and focal loss (gamma configured per
experiment). Originally initialized with standard cross-entropy, see D-20260916-LP-1.

## Experiments

### Cross-Entropy Baseline {#E1}
**Purpose:** Establish a baseline classifier before addressing class imbalance.
**Assessment:** Per-class precision/recall, confusion matrix on the validation split.
**Results:** Model converged to predicting NEUTRAL almost exclusively, confirming
severe class imbalance degrades the baseline (run 2026-09-12).

### Focal Loss Ablation {#E2}
**Purpose:** Test whether focal loss recovers signal on the minority UP/DOWN classes.
**Assessment:** Same per-class precision/recall as E1, compared against the baseline.
