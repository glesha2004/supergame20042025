# SpaceGrid Arena

Prototype for a top‑down arena shooter written in **pygame**. The project is
based on a large design document and currently implements a very small subset
of the planned features:

* basic player ship controlled with WASD
* simple AI bots that seek and capture points
* four capture points that require ten seconds to take
* yellow spike hazards in the corners that instantly destroy ships

## Running

```bash
python main.py        # run normally
python - <<'PY'
import main
main.main(max_frames=10)  # run ten frames for testing
PY
```

Game behaviour can be tweaked in `config/game_config.json`.
