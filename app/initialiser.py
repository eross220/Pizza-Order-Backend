from app.db.database.initialise import initialise
from app.db.database.session import SessionLocal
from sqlalchemy.orm import Session

def init(db:Session) -> None:
    print("Initialising database...")
    initialise(db)


def main() -> None:
    init()


if __name__ == "__main__":
    main()
