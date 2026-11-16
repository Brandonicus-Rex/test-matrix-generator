# Test matrix: Fictional mobile catalog

| | |
|---|---|
| Strategy | 3-wise |
| Coverage strength | 3 (triples) |
| Seed | 0 |
| Parameters | 6 (plan, device, voicemail, mms, intl, hotspot) |
| Rules | 5 |
| Combinations before rules | 144 |
| Valid combinations (exhaustive) | 63 |
| **Tests generated** | **22** |
| Reduction vs exhaustive | 65% fewer tests |
| Coverable triples | 205 |
| Covered | 205 (100.0%) |
| Impossible under the rules | 43 |

## Rules

- `device == 'iot' -> voicemail == 'off'`
- `device == 'iot' -> mms == 'off'`
- `device == 'tablet' -> voicemail == 'off'`
- `plan == 'basic' -> hotspot == 'off'`
- `intl == 'on' -> plan in ['plus', 'unlimited']`

## Tests

| # | plan | device | voicemail | mms | intl | hotspot |
|---|---|---|---|---|---|---|
| 1 | plus | phone | off | off | off | on |
| 2 | unlimited | tablet | off | off | on | off |
| 3 | unlimited | phone | on | on | off | off |
| 4 | basic | iot | off | off | off | off |
| 5 | plus | phone | on | on | on | on |
| 6 | unlimited | tablet | off | on | off | on |
| 7 | plus | tablet | off | on | on | off |
| 8 | unlimited | phone | on | off | on | on |
| 9 | plus | iot | off | off | on | on |
| 10 | basic | phone | on | off | off | off |
| 11 | basic | phone | off | on | off | off |
| 12 | plus | tablet | off | off | off | off |
| 13 | unlimited | iot | off | off | off | on |
| 14 | plus | phone | on | off | on | off |
| 15 | basic | tablet | off | off | off | off |
| 16 | unlimited | iot | off | off | on | off |
| 17 | unlimited | phone | off | on | on | off |
| 18 | plus | phone | on | on | off | on |
| 19 | plus | tablet | off | off | on | on |
| 20 | plus | iot | off | off | off | off |
| 21 | basic | phone | on | on | off | off |
| 22 | basic | tablet | off | on | off | off |

## Triples the rules make impossible

- plan=basic, device=tablet, voicemail=on
- plan=basic, device=iot, voicemail=on
- plan=plus, device=tablet, voicemail=on
- plan=plus, device=iot, voicemail=on
- plan=unlimited, device=tablet, voicemail=on
- plan=unlimited, device=iot, voicemail=on
- plan=basic, device=iot, mms=on
- plan=plus, device=iot, mms=on
- plan=unlimited, device=iot, mms=on
- plan=basic, device=phone, intl=on
- plan=basic, device=tablet, intl=on
- plan=basic, device=iot, intl=on
- plan=basic, device=phone, hotspot=on
- plan=basic, device=tablet, hotspot=on
- plan=basic, device=iot, hotspot=on
- plan=basic, voicemail=on, intl=on
- plan=basic, voicemail=off, intl=on
- plan=basic, voicemail=on, hotspot=on
- plan=basic, voicemail=off, hotspot=on
- plan=basic, mms=on, intl=on
- plan=basic, mms=off, intl=on
- plan=basic, mms=on, hotspot=on
- plan=basic, mms=off, hotspot=on
- plan=basic, intl=on, hotspot=on
- plan=basic, intl=on, hotspot=off
- plan=basic, intl=off, hotspot=on
- device=tablet, voicemail=on, mms=on
- device=tablet, voicemail=on, mms=off
- device=iot, voicemail=on, mms=on
- device=iot, voicemail=on, mms=off
- device=iot, voicemail=off, mms=on
- device=tablet, voicemail=on, intl=on
- device=tablet, voicemail=on, intl=off
- device=iot, voicemail=on, intl=on
- device=iot, voicemail=on, intl=off
- device=tablet, voicemail=on, hotspot=on
- device=tablet, voicemail=on, hotspot=off
- device=iot, voicemail=on, hotspot=on
- device=iot, voicemail=on, hotspot=off
- device=iot, mms=on, intl=on
- device=iot, mms=on, intl=off
- device=iot, mms=on, hotspot=on
- device=iot, mms=on, hotspot=off
