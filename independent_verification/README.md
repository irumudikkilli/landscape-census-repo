# Independent verification (third-party)

`ThreePortCensus-IndependentVerifier.py` was written by an **independent reviewer**
during an adversarial read of the manuscript on 20 June 2026 — **not by the
author**. It re-implements the three-port (*n* = 3) census from scratch in exact
rational arithmetic using **only the Python standard library** (no `pycddlib`, no
third-party packages), and independently reproduces:

- 240 signed-ideal / 16 non-ideal families out of 256;
- 22 orbits under the signed coordinate group B₃;
- the 16 non-ideal families splitting into two orbits of 8;
- the unique fractional vertex (½, ½, ½).

Recorded output (`ThreePortCensus-IndependentVerifier-output.txt`):

```
PASS: all manuscript n=3 census targets reproduced exactly.
```

Run it yourself:

```sh
python3 ThreePortCensus-IndependentVerifier.py
```

A separate reimplementation, on a different code path, reaching the same exact
counts is the strongest available evidence that the *n* = 3 results are facts
about the mathematics rather than artifacts of one program.
