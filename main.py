import logging

from app.cli.app import App
from app.config import DB_PATH, LOG_PATH
from app.database import Database


def main() -> None:
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    db = Database(DB_PATH)
    try:
        db.initialise()
        App(db).run()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
