# 8 Ball Project Report

This directory contains the LaTeX source for the final project report.

## Contents

- `project_report.tex` - Main LaTeX document with comprehensive project documentation
- `presentation.tex` - Beamer slides for 5-minute presentation with live demo

## Compiling the Documents

### Compiling the Report

### Prerequisites

You need a LaTeX distribution installed:

- **macOS**: Install [MacTeX](https://www.tug.org/mactex/)
  ```bash
  brew install --cask mactex
  ```

- **Linux**: Install TeX Live
  ```bash
  sudo apt-get install texlive-full  # Ubuntu/Debian
  sudo yum install texlive-scheme-full  # Fedora/RHEL
  ```

- **Windows**: Install [MiKTeX](https://miktex.org/download)

### Compilation Commands

```bash
cd report

# Basic compilation
pdflatex project_report.tex

# Full compilation with references (run twice for TOC)
pdflatex project_report.tex
pdflatex project_report.tex

# Clean auxiliary files
rm -f *.aux *.log *.out *.toc
```

### Compiling the Presentation

```bash
cd report

# Compile Beamer slides
pdflatex presentation.tex

# Run twice for proper slide numbers
pdflatex presentation.tex
pdflatex presentation.tex

# Clean auxiliary files
rm -f *.aux *.log *.out *.nav *.snm *.toc
```

The presentation outputs `presentation.pdf` with:
- 6 main slides (2 minutes of talking)
- Space for 3+ minute live demo
- 2 backup slides for Q&A

**Presentation Structure:**
1. Title slide with team members
2. Problem statement and tech stack
3. System architecture diagram
4. Key features (transitions to live demo)
5. Performance metrics and bottlenecks
6. Lessons learned and future work

### Report Output

The compilation produces `project_report.pdf` which includes:

1. **Title Page** - Project title and team members (update names in the LaTeX file)
2. **Table of Contents** - Auto-generated section navigation
3. **Project Overview** - Participants, goals, and accomplishments
4. **System Components** - Software/hardware stack with versions
5. **Architecture Diagram** - TikZ-generated visual system diagram
6. **Component Interactions** - Detailed data flow descriptions
7. **Debugging & Testing** - Methodology and test results
8. **Performance Analysis** - Benchmarks, bottlenecks, and scalability
9. **Lessons Learned** - Technical challenges and solutions
10. **Future Work** - Potential enhancements

## Customization

### Update Team Information

Edit lines 34-39 in `project_report.tex`:

```latex
\author{
    Your Name 1 \\
    Your Name 2 \\
    Your Name 3 \\
    \texttt{email@berkeley.edu}
}
```

And lines 55-59 for roles:

```latex
\item \textbf{[Name]} -- Role: [e.g., Backend Development]
\item \textbf{[Name]} -- Role: [e.g., Frontend Development]
\item \textbf{[Name]} -- Role: [e.g., DevOps, System Integration]
```

### Add Screenshots

To add screenshots of the application:

1. Save images to the `report/` directory (e.g., `screenshot_dashboard.png`)
2. Add figure code in LaTeX:

```latex
\begin{figure}[H]
\centering
\includegraphics[width=0.8\textwidth]{screenshot_dashboard.png}
\caption{8 Ball Dashboard Homepage}
\label{fig:dashboard}
\end{figure}
```

### Adjust Architecture Diagram

The TikZ diagram is in Section 4.1 (lines 240-310). You can:

- Change colors: `fill=blue!20`, `fill=green!20`
- Adjust positions: `below=of`, `below left=1.5cm and 1cm of`
- Modify arrow styles: `arrow/.style={-{Stealth[length=3mm]}, thick}`

## Document Structure

### Report Sections Summary

| Section | Content | Pages |
|---------|---------|-------|
| 1-2 | Title, TOC, Participants | 2 |
| 3 | Project Goals & Achievements | 2 |
| 4 | Software/Hardware Components | 2 |
| 5 | System Architecture & Diagrams | 3 |
| 6 | Component Interactions | 4 |
| 7 | Debugging & Testing | 3 |
| 8 | Performance & Bottlenecks | 4 |
| 9-11 | Lessons, Future Work, Conclusion | 2 |

**Total: ~22 pages**

### Presentation Slides Summary

| Slide # | Content | Time |
|---------|---------|------|
| 1 | Title and team information | 10s |
| 2 | Problem statement and tech stack | 30s |
| 3 | System architecture diagram | 30s |
| 4 | Key features (transition to demo) | 20s |
| 5 | Performance metrics and bottlenecks | 30s |
| 6 | Lessons learned and future work | 20s |
| Backup 1 | Infrastructure as Code details | - |
| Backup 2 | Database schema details | - |

**Total Slides: 6 main + 2 backup**
**Talk Time: ~2 minutes + 3 minute demo = 5 minutes**

## Common LaTeX Errors

### Missing Package

```
! LaTeX Error: File `tikz.sty' not found.
```

**Fix**: Install missing packages
```bash
# macOS
sudo tlmgr install tikz pgf

# Ubuntu/Debian
sudo apt-get install texlive-pictures
```

### Undefined Control Sequence

```
! Undefined control sequence.
l.123 \usetikzlibrary
```

**Fix**: Ensure all `\usepackage` commands are before `\begin{document}`

### Overfull hbox

```
Overfull \hbox (15.0pt too wide) in paragraph at lines 456--457
```

**Fix**: This is just a warning. LaTeX couldn't fit text in the line width. Usually safe to ignore, or add `\linebreak` manually.

## Online LaTeX Editors

If you prefer not to install LaTeX locally:

- **Overleaf**: https://www.overleaf.com/ (free account, collaborative editing)
- **Papeeria**: https://papeeria.com/
- **CoCalc**: https://cocalc.com/

Upload `project_report.tex` and compile online.

## Citation

If you reference this work:

```bibtex
@misc{8ball2025,
  title={8 Ball: Real-Time NBA Analytics Platform},
  author={[Your Names]},
  year={2025},
  note={UC Berkeley - Datacenter Scale Computing Final Project}
}
```

## License

This report is for academic purposes only. All NBA data sourced from NBA Stats API. Team logos and player images © NBA.
