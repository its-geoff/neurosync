# NeuroSync

> This project uses an EEG headband with connected software to filter brainwaves and translate them to emotions.

## Team

| Name | GitHub | Email |
|------|--------|-------|
| Geoffrey Agustin | [@its-geoff](https://github.com/its-geoff) | geoffrey.agustin@sjsu.edu |
| Jairo Manansala | [@jairomanansala](https://github.com/jairomanansala) | jairo.manansala@sjsu.edu |
| Garrett Miller | [@GaM1404](https://github.com/GaM1404) | garrett.miller@sjsu.edu |
| Uyen Vu (Hillary Vu) | [@spicyMcChickens](https://github.com/spicyMcChickens) | uyen.vu02@sjsu.edu |

**Advisor:** Charan Bhaskar

---

## Problem Statement

[2-3 sentences describing the problem you're solving and why it matters]

## Solution

[2-3 sentences describing your solution approach]

### Key Features

- Feature 1
- Feature 2
- Feature 3

---

## Demo

[Link to demo video or GIF]

**Live Demo:** [URL if deployed]

---

## Screenshots

| Feature | Screenshot |
|---------|------------|
| [Feature 1] | ![Screenshot](docs/screenshots/feature1.png) |
| [Feature 2] | ![Screenshot](docs/screenshots/feature2.png) |

---

## Tech Stack

### Hardware
| Category | Technology |
|----------|------------|
| Language | SystemVerilog |
| FPGA Board | Diligent Nexys A7-100T |
| EEG headband | Muse 2 |

### Software
| Category | Technology |
|----------|------------|
| Language | Python 3.13.* |
| Package Management | uv |
| Signal Processing | SciPy, NumPy |
| Data I/O | pyserial, muselsl/pylsl |
| Testing | PyTest |

---

## Getting Started

### Prerequisites

- Python v3.13.*
- uv v0.4+
- Muse 2 headband

### Installation

```bash
# Clone the repository
git clone https://github.com/neurosync.git
cd neurosync

# Install package manager (uv)
curl -LsSf https://astral.sh/uv/install.sh | sh     # macOS / Linux
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.sh | iex"   # Windows (PowerShell)

# Set up virtual environment
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# Install dependencies
cd software/
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
pytest
```

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

---

## Acknowledgments

- Charan Bhaskar, for guidance and input on project progress and documentation

---

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

*CMPE 195A/B - Senior Design Project | San Jose State University | Spring 2026*