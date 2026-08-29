# Target exercise formats

Taken from real LernWolf.de Klasse 4 worksheets the user supplied. Phase 2's
generators produce these shapes, not free-form prose questions.

## 1. Rechentabellen (operation grids)

A grid with an operator in the corner, column headers across the top and row
headers down the side; the child fills every cell.

```
  ·  |  5   2   10   7   1          -   |  8   65  130  180  260
 100 |                              860 |
  50 |                              330 |
 350 |                              640 |
 500 |                              710 |
```

Trivially generated and checked in Python. Difficulty is controlled by the
header values, not by the format.

## 2. Malpyramiden / Zahlenmauern (multiplication pyramids)

Adjacent cells multiply into the cell above. Two directions, and the second
is the interesting one:

- **Forward** - the bottom row is given, the child works upward.
- **Inverse** - the apex and some middle cells are given and the bottom is
  blank, so the child must divide to work back down.

```
        [ ]                  [720]
      [ ] [ ]              [12] [ ]
    [2] [6] [5]           [2] [ ] [ ]
```

Inverse pyramids are the strongest argument for generating these in Python.
They need consistent backward solving, and a model that gets one wrong marks a
child wrong for being right.

## 3. Zahlenraum 1000: plus, minus, mal, geteilt

Plain column exercises, including **division with remainder** rendered in the
German convention:

```
 784 - 169 = ____        159 : 8 = ____ R ____
 850 : 5   = ____        733 : 5 = ____ R ____
```

Note `:` for division and `R` for the remainder - a child who writes "19 R 7"
is right and must be graded right.

## Consequences for the curriculum

`curriculum.py` needs two topics it does not have yet: `rechentabellen` and
`zahlenmauern`. `schriftlich` should cover division with remainder explicitly.
