# DOS — Decision Operating System

## 1. Problems
### New Problems
What problems need a solution?

### Existing Problems
What existing solutions/problems need a better solution?

---

## 2. Decisions
### New Decisions
What decisions can/need to be made now to solve the problems?

### Existing Decisions
What existing decisions can/need to be improved, changed, or extended now?

---

## 3. Solutions
### Implemented
What solutions are already implemented?

### Ready to Implement
What solutions have been decided and can be implemented now?

### Not Yet Decided
What solutions/approaches are still undecided?

---

## 4. Continuous Improvement
Cycle:

Problem
→ Decision
→ Solution
→ Implementation
→ Observe
→ Improve
→ Repeat

---

## 5. Approach
fs-systsm

/DOS/
├── DOS.md
├── ds.txt
└── nn[project-name]/
    ├── ds.txt
    ├── nn[problem-name].txt
    └── nn[folder]/
        ├── ds.txt
        ├── nn[problem-name].txt
        └── nn[folder]
            ├── ds.txt
            └── nn[problem-name].txt

---

### Rules
First Number
0 = decision impossible
1 = decision possible
2 = implementation impossible
3 = implementation possible
4 = implemented
Second Number
if implemented (3): rate 0-4 based on confidence level 
if not implemented (0-2): rate 0-4 based on priority level 
- No capitalization allowed

```33[folder name]/42[problem-name].txt
[what]:
    note
```

- ds.txt = division specification

```ds.txt
[problem-name]:
    note
[folder name]:
    note
[folder name]:
    note
[folder name]:
    note
[folder name]:
    note
```
