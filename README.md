# md2docx — Markdown & AI to Word Converter

[![Open Source](https://img.shields.io/badge/open--source-free-brightgreen)](https://github.com/markovrv/md2docx)
[![Python](https://img.shields.io/badge/python-3.10-blue)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED)](https://docker.com)
[![Demo](https://img.shields.io/badge/demo-online-4A90D9)](https://md2docx.markovrv.ru)

**md2docx** converts Markdown with LaTeX formulas into valid `.docx` files with **editable Word equations** (OMML). Paste Markdown — get a ready-to-edit Word document.

> **[Демо-версия: md2docx.markovrv.ru](https://md2docx.markovrv.ru)**

---

## Features

- **Rich Markdown** — headings, bold, italic, strikethrough, code, links, images, tables
- **Editable Word equations** — LaTeX formulas become native OMML (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`) editable in Word's equation editor
- **Tables** — with borders and header row highlighting
- **Code blocks** — monospace with gray background
- **Blockquotes** — indented with left border, italic
- **Lists** — ordered and unordered, up to three nesting levels
- **Two-panel UI** — left side Markdown editor, right side live preview with KaTeX rendering
- **Resizable panels** — drag the divider to adjust
- **Docker support** — one command to deploy anywhere

---

## Screenshot

```
┌──────────────────────────────────────────────────────────────────┐
│  MD → DOCX  │  Markdown & AI to Word Converter  [Download] ...  │
├────────────────────────┬──┬──────────────────────────────────────┤
│ Исходный Markdown     │▐▐│  Форматированный текст               │
│                        │▐▐│                                      │
│ # Title                │▐▐│  Title                               │
│ **Bold** text          │▐▐│  Bold text                           │
│ $E=mc^2$              │▐▐│  𝐸 = 𝑚𝑐²                            │
│                        │▐▐│                                      │
│ | A | B |              │▐▐│  ┌───┬───┐                           │
│ |---|---|              │▐▐│  │ A │ B │                           │
│ | 1 | 2 |              │▐▐│  ├───┼───┤                           │
│                        │▐▐│  │ 1 │ 2 │                           │
│                        │▐▐│  └───┴───┘                           │
├────────────────────────┴──┴──────────────────────────────────────┤
│  ████████░░░░░░░░░░░░░░░░░░░░  Resizer  ░░░░░░░░░░░░░░░░░░░░░░░░ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Flask 3 |
| Markdown parsing | `markdown` lib (extra ext.) |
| LaTeX → OMML | `latex2mathml` + custom MathML→OMML converter |
| DOCX generation | `python-docx` |
| Formula fallback | `matplotlib` (Agg backend, image) |
| Client preview | `marked.js` + `KaTeX` (CDN) |
| Production WSGI | `waitress` |
| Container | Docker + Compose |

---

## Quick Start

### Local

```bash
git clone https://github.com/markovrv/md2docx.git
cd md2docx
python -m venv venv
source venv/bin/activate   # or: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

### Docker

```bash
git clone https://github.com/markovrv/md2docx.git
cd md2docx
docker compose up -d --build
```

Open `http://localhost:5000`. The container runs `waitress` (production WSGI) with healthcheck.

---

## Project Structure

```
md2docx/
├── app.py                 # Flask server
├── converter.py           # Markdown → DOCX converter
├── omml.py                # LaTeX → OMML (Word equations)
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose config
├── .dockerignore          # Docker build exclusions
├── .gitignore             # Git exclusions
├── static/
│   └── style.css          # Dark theme UI styles
└── templates/
    └── index.html         # Web interface (two-panel editor)
```

---

## LaTeX Formula Support

Formulas are converted to **editable Word equations** using OMML (Office Math Markup Language). All four standard delimiter syntaxes are supported:

| Syntax | Type | Example |
|--------|------|---------|
| `$...$` | Inline | `$E = mc^2$` |
| `$$...$$` | Display (block) | `$$\int_a^b f(x)\,dx$$` |
| `\(...\)` | Inline | `\(E = mc^2\)` |
| `\[...\]` | Display (block) | `\[\int_a^b f(x)\,dx\]` |

Supported constructs: fractions, superscripts/subscripts, roots, integrals, sums, limits, Greek letters, matrices, and more.

---

## API

### `POST /convert`

Converts Markdown to DOCX.

```
POST /convert
Content-Type: application/json

{"markdown": "# Hello\n\n**Bold** and $E=mc^2$"}
```
Returns: `.docx` file (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`)

### `POST /preview`

Converts Markdown to HTML for server-side preview.

```
POST /preview
Content-Type: application/json

{"markdown": "# Hello"}
```
Returns: `{"html": "<h1>Hello</h1>"}`

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PRODUCTION` | `1` (Docker) | Enables `waitress` WSGI server |
| `MPLBACKEND` | `Agg` | Matplotlib non-GUI backend |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `5000` | Listen port |

---

## License

MIT — свободное использование, модификация и распространение.

**Автор:** [markovrv](https://github.com/markovrv)  
**Демо:** [md2docx.markovrv.ru](https://md2docx.markovrv.ru)
