from booking_history.app import create_app


async def main() -> None:
    app = create_app()
    await app.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
