from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

engine = create_engine("sqlite:///./replaylab.db", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
