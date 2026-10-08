import asyncio

from booking.app import run_app


def main() -> None:
    asyncio.run(run_app())


if __name__ == "__main__":
    main()
