# Numerai Public Benchmark Trail

This note prepares the first external benchmark layer for the public financial ML portfolio.
It does not submit predictions, stake NMR, or claim performance.

## Why This Exists

The existing public repo already shows validation, serving, monitoring, and experiment logs.
Numerai adds an external benchmark trail that recruiters can understand quickly.

## Current Format Assumptions

- Numerai Tournament submissions use an `id` column and a `prediction` column.
- Tournament predictions are float values between 0 and 1.
- Numerai Signals submissions use a valid ticker column and a `signal` column.
- Signals values must be in the open interval `(0, 1)`.
- Live Signals submissions need at least 100 valid universe tickers.

## Public / Private Boundary

Public:

- submission format validation
- synthetic examples
- validation notes
- tracker updates
- first-submission receipt once created

Private:

- live trading rules
- broker integration
- account details
- private alpha features
- exact production thresholds

## Synthetic Tournament CSV Preview

```csv
id,prediction
n00000,0.008264462809917356
n00001,0.371900826446281
n00002,0.7355371900826446
n00003,0.10743801652892562
n00004,0.4793388429752066
```

## Synthetic Signals CSV Preview

```csv
numerai_ticker,signal
US00000,0.008264462809917356
US00001,0.2066115702479339
US00002,0.39669421487603307
US00003,0.5867768595041323
US00004,0.7768595041322314
```

## Next Manual Step

1. Create or confirm Numerai account.
2. Create a model id.
3. Generate a real live prediction file from the current Numerai live dataset.
4. Upload manually first.
5. Record the receipt in `2026/trackers/numerai_progress.csv`.

## Interview Message

The goal of this step is not to overclaim a score.
The goal is to create an external, reproducible benchmark trail for financial ML validation.
