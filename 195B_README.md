# NeuroSync

> This project uses an EEG headband with connected software to filter brainwaves and translate them to emotions.

## Status

![Python CI/CD](https://github.com/its-geoff/neurosync/actions/workflows/python-ci.yaml/badge.svg)
[![codecov](https://codecov.io/gh/its-geoff/neurosync/branch/main/graph/badge.svg?token=JBGWUQ796L)](https://codecov.io/gh/its-geoff/neurosync)

## Team

| Name                 | GitHub                                                 | Email                     |
| -------------------- | ------------------------------------------------------ | ------------------------- |
| Geoffrey Agustin     | [@its-geoff](https://github.com/its-geoff)             | geoffrey.agustin@sjsu.edu |
| Jairo Manansala      | [@jairomanansala](https://github.com/jairomanansala)   | jairo.manansala@sjsu.edu  |
| Garrett Miller       | [@GaM1404](https://github.com/GaM1404)                 | garrett.miller@sjsu.edu   |
| Uyen Vu (Hillary Vu) | [@spicyMcChickens](https://github.com/spicyMcChickens) | uyen.vu02@sjsu.edu        |

**Advisor:** Charan Bhaskar

---

## Problem Statement

Emotions are complex; students may have trouble comprehending their emotional state to mental health professionals. Traditional counseling oftentimes relies heavily on verbal communication and subjective observation, making it difficult to accurately gauge real time emotional and cognitive state.

## Solution

NeuroSync addresses the problem by utilizing electroencephalogram (EEG) technology along with Field Programmable Gate Array (FPGA) based processing in order to interpret, visualize, and analyze emotional states concurrently. This product will enhance the quality of counseling sessions and leave students feeling more fulfilled after talking to mental health professionals. This system aims to ensure that counseling be responsive, accurate, and effective.

### Key Features

- Real-time EEG signal acquisition and band power calculation
- Hardware-accelerated brainwave visualization on FPGA
- Multi-dimensional emotional state mapping (in progress)

---

## Demo

[Link to demo video or GIF]

**Live Demo:** [URL if deployed]

---

## Screenshots

| Feature     | Screenshot                                   |
| ----------- | -------------------------------------------- |
| [Feature 1] | ![Screenshot](docs/screenshots/feature1.png) |
| [Feature 2] | ![Screenshot](docs/screenshots/feature2.png) |

---

## Tech Stack

### Hardware

| Category               | Technology             |
| ---------------------- | ---------------------- |
| Language               | SystemVerilog          |
| Communication Protocol | UART                   |
| FPGA Board             | Diligent Nexys A7-100T |
| EEG headband           | Muse 2                 |

### Software

| Category                     | Technology              |
| ---------------------------- | ----------------------- |
| Language                     | Python 3.13.\*          |
| Package Management           | uv                      |
| Signal Processing            | SciPy, NumPy            |
| Data Formatting and Analysis | pandas                  |
| Data I/O                     | pyserial, muselsl/pylsl |
| Testing                      | PyTest                  |

---

## Getting Started

### Prerequisites

- Python v3.13.\*
- uv v0.4+
- Muse 2 headband

### Installation

```bash
# Clone the repository
git clone https://github.com/neurosync.git
cd neurosync

# Install package manager (uv)
curl -LsSf https://astral.sh/uv/install.sh | sh     # macOS / Linux
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows (PowerShell)

# Set up virtual environment
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# Install dependencies
cd software/
chmod +x scripts/*
# Before the next step, make sure neurosync/software/scripts is added to PATH
./install-liblsl
uv sync
```

### Running Locally

```bash
cd software/src/
python3 main.py
```

### Running Tests

```bash
cd software/
pytest -v
```

To run with coverage locally:

```bash
cd software/
uv run pytest -v --cov=src --cov-report=term-missing --cov-report=html
# Open htmlcov/index.html in your browser for a full line-by-line report
```

Coverage reports are automatically uploaded to [Codecov](https://codecov.io/gh/<org-or-user>/neurosync) on every push to `main` and on pull requests.

---

## Project Structure

```
.
├── .github/                       # GitHub workflows
├── hardware/                      # FPGA EEG visualization (SystemVerilog)
├── software/                      # data processing and transmission to FPGA
├── .gitignore
├── LICENSE                        # Apache-2.0 License
└── README.md
```

---

## Contributing

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'Add amazing feature'`)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### Commit Messages

Use clear, descriptive commit messages:

- `Add user authentication endpoint`
- `Fix database connection timeout issue`
- `Update README with setup instructions`

## Documentation

- [Architecture](docs/architecture.md)

---

## Acknowledgments

- Charan Bhaskar, for guidance and input on project progress and documentation

---

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

_CMPE 195A/B - Senior Design Project | San Jose State University | Spring 2026_
