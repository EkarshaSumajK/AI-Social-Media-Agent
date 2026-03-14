import asyncio
import subprocess
import sys

from app.services.user_service import ensure_admin_user


async def main() -> None:
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], check=True)
    await ensure_admin_user()
    print('Alembic migrations applied and admin user ensured.')


if __name__ == '__main__':
    asyncio.run(main())
