# MS-DOS

**MS-DOS** is a personal operating system for **decisions, projects, and execution**, built to run inside **Termux**.

It combines two systems:

- **DOS — Decision Operating System**: a structured system for making, recording, reviewing, and improving decisions.
- **Mori Studio (MS)**: a web-based virtual studio for managing projects, working with an AI assistant, and automatically pushing changes to GitHub repositories.

The goal is to create a single environment where you can **think → decide → build → review → improve**.

---

## Architecture

```text
~/ms-dos/
│
├── main.py                 # Main launcher
│
├── dos.py                  # Decision Operating System backend
├── dos.html                # DOS web interface
├── DOS.md                  # DOS documentation
│
├── ms.py                   # Mori Studio backend
├── ms.html                 # Mori Studio web interface
│
├── dos/                    # DOS data root
│   └── ...                 # Decisions, problems, etc.
│
└── projects/               # Mori Studio project root
    └── ...                 # Your projects
```

### Two Separate Roots

MS-DOS uses two independent storage roots:

```text
~/ms-dos/dos/
```

is the root directory for the **Decision Operating System**.

```text
~/ms-dos/projects/
```

is the root directory for **Mori Studio projects**.

This separation keeps **decision-making** and **project implementation** organized while allowing them to work together.

---

# DOS — Decision Operating System

DOS is a system for externalizing and managing decisions.

It can be used to make decisions about **anything**, including:

- Life
- Career
- Education
- Relationships
- Personal development
- Programming
- Software architecture
- Projects
- Business
- Systems
- Productivity
- Daily problems
- Long-term goals

Instead of keeping decisions in your head, DOS provides a structured place to record them.

### The basic idea

```text
PROBLEM
   ↓
DECISION
   ↓
SOLUTION
   ↓
IMPLEMENTATION
   ↓
REVIEW
   ↓
IMPROVEMENT
```

DOS helps answer questions such as:

```text
What problem am I solving?

What decision needs to be made?

What have I already decided?

What has not been decided yet?

Why did I make this decision?

What should be implemented?

What has already been implemented?

Should an existing decision be reconsidered?
```

The system can therefore be used as a **Decision Operating System for life and work**, rather than being limited to software development.

---

# Mori Studio

**Mori Studio (MS)** is the web-based virtual studio component of MS-DOS.

It uses:

```text
~/ms-dos/projects/
```

as its project root.

Mori Studio is designed to provide a workspace for building and managing projects through a web interface.

It includes:

- Project management
- Web-based virtual studio
- AI assistance
- Project file management
- Development workflow
- GitHub integration
- Automatic push to repositories

The idea is to make the process of going from an idea to an implemented project more direct:

```text
IDEA
 ↓
DECISION
 ↓
PROJECT
 ↓
IMPLEMENTATION
 ↓
GITHUB
```

---

# Web Interface

Both systems run locally through Termux.

The main system runs on:

```text
http://localhost:8000
```

After starting the system, open the web interface from your browser.

---

# Requirements

You need:

- **Android**
- **Termux**
- Python 3
- Git (for GitHub-related functionality)

The system is designed around the following Termux home directory:

```text
~
```

The repository must be placed at:

```text
~/ms-dos/
```

---

# Installation

Clone or copy this repository into the root of your Termux home directory.

The final structure should be:

```text
~/ms-dos/
```

For example:

```bash
cd ~
git clone <repository-url> ms-dos
```

Or manually place the repository at:

```text
~/ms-dos
```

---

# Existing DOS Data

If you already have an existing DOS system, place your existing DOS files inside:

```text
~/ms-dos/dos/
```

For example:

```text
~/ms-dos/dos/
├── ...
├── ...
└── ...
```

Do not place existing DOS data directly beside `dos.py`.

---

# Existing Projects

Place your existing projects inside:

```text
~/ms-dos/projects/
```

For example:

```text
~/ms-dos/projects/
├── project-one/
├── project-two/
└── project-three/
```

Mori Studio treats this directory as its **project root**.

---

# Running MS-DOS

Once the repository is located at:

```text
~/ms-dos/
```

run:

```bash
python3 ~/ms-dos/main.py
```

You can run this command **from anywhere in Termux**.

For example:

```bash
cd ~
python3 ~/ms-dos/main.py
```

or:

```bash
cd /tmp
python3 ~/ms-dos/main.py
```

The launcher automatically locates `ms.py` and `dos.py` relative to `main.py`.

---

# Main Launcher

`main.py` starts both systems:

```text
main.py
   │
   ├── ms.py
   │
   └── dos.py
```

It also makes sure the required directories exist:

```text
~/ms-dos/projects/
~/ms-dos/dos/
```

If they do not exist, they are created automatically.

---

# Data Structure

The important separation is:

```text
~/ms-dos/
│
├── dos/
│   └── DOS data
│
└── projects/
    └── Project data
```

### DOS

```text
~/ms-dos/dos/
```

**Purpose:** thinking, decisions, problems, and decision-related information.

### Mori Studio

```text
~/ms-dos/projects/
```

**Purpose:** projects, implementation, development, and project files.

---

# Philosophy

MS-DOS is built around the idea that **thinking and implementation should be externalized**.

Instead of trying to remember everything:

```text
THINK
 ↓
WRITE
 ↓
DECIDE
 ↓
IMPLEMENT
 ↓
REVIEW
```

The system provides a persistent environment for this process.

DOS manages the **decision layer**.

Mori Studio manages the **project and implementation layer**.

Together:

```text
                 MS-DOS
                    │
        ┌───────────┴───────────┐
        │                       │
       DOS                MORI STUDIO
        │                       │
   Decisions                 Projects
   Problems                  Coding
   Reasoning                 AI
   Reviews                   GitHub
        │                       │
        └───────────┬───────────┘
                    │
               IMPLEMENTATION
                    │
                  RESULT
                    │
                 REVIEW
                    │
                IMPROVEMENT
```

---

# Quick Start

After installing:

```bash
cd ~/ms-dos
python3 main.py
```

Then open:

```text
http://localhost:8000
```

Your system is now running.

---

# Repository Structure

```text
ms-dos/
│
├── README.md
├── DOS.md
│
├── main.py
│
├── dos.py
├── dos.html
│
├── ms.py
├── ms.html
│
├── dos/
│   └── DOS data
│
└── projects/
    └── Your projects
```

---

## MS-DOS

**Decision Operating System + Mori Studio**

A local Termux-based environment for:

> **Deciding what to do, building what was decided, and continuously improving the system.**
