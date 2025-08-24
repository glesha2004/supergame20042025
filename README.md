# SpaceGrid Arena Prototype

This repository contains a minimal Python/pygame project skeleton based on the
"SpaceGrid Arena" technical specification. The current code focuses on project
structure and simple placeholders without gameplay features.

## Running

```bash
python main.py
```

The game opens a blank pygame window and draws placeholder capture points.

## Repository layout

- `main.py` – entry point.
- `src/` – Python packages with stubs for game systems.
- `config/` – default configuration (`game_config.json`).
- `assets/` – placeholder for fonts and sound effects. Binary assets are
  intentionally excluded from the repository.
- `saves/` – placeholder for save files.

## Development Notes

Binary assets like audio or fonts are not included to avoid issues with
version control restrictions. Use the directories as drop-in locations for
such assets during development.
