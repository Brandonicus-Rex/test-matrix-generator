# Test matrix: Fictional mobile catalog

| | |
|---|---|
| Strategy | Pairwise |
| Coverage strength | 2 (pairs) |
| Seed | 0 |
| Parameters | 6 (plan, device, voicemail, mms, intl, hotspot) |
| Rules | 5 |
| Combinations before rules | 144 |
| Valid combinations (exhaustive) | 63 |
| **Tests generated** | **10** |
| Reduction vs exhaustive | 84% fewer tests |
| Coverable pairs | 76 |
| Covered | 76 (100.0%) |
| Impossible under the rules | 5 |

## Rules

- `device == 'iot' -> voicemail == 'off'`
- `device == 'iot' -> mms == 'off'`
- `device == 'tablet' -> voicemail == 'off'`
- `plan == 'basic' -> hotspot == 'off'`
- `intl == 'on' -> plan in ['plus', 'unlimited']`

## Tests

| # | plan | device | voicemail | mms | intl | hotspot |
|---|---|---|---|---|---|---|
| 1 | plus | tablet | off | off | off | off |
| 2 | plus | phone | on | on | on | on |
| 3 | unlimited | iot | off | off | on | on |
| 4 | unlimited | phone | on | on | off | off |
| 5 | basic | iot | off | off | off | off |
| 6 | unlimited | tablet | off | on | on | on |
| 7 | basic | phone | on | off | off | off |
| 8 | plus | iot | off | off | on | off |
| 9 | basic | tablet | off | on | off | off |
| 10 | unlimited | phone | off | on | off | on |

## Pairs the rules make impossible

- plan=basic, intl=on
- plan=basic, hotspot=on
- device=tablet, voicemail=on
- device=iot, voicemail=on
- device=iot, mms=on
