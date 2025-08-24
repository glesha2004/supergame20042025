from src.config import load_config
from src.game import Game


def main(max_frames: int | None = None) -> None:
    cfg = load_config()
    game = Game(cfg)
    game.run(max_frames=max_frames)


if __name__ == "__main__":
    main()
