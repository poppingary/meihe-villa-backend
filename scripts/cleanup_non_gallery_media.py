#!/usr/bin/env python3
"""One-off script: remove media DB records whose s3_key is NOT under images/gallery/.

Only deletes database records — S3 files are left untouched because they are
referenced directly by other pages (heritage, about, hero, etc.).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models.media import MediaFile

GALLERY_PREFIX = "images/gallery/"


async def main():
    async with AsyncSessionLocal() as db:
        stmt = delete(MediaFile).where(
            ~MediaFile.s3_key.startswith(GALLERY_PREFIX)
        )
        result = await db.execute(stmt)
        await db.commit()
        print(f"Deleted {result.rowcount} non-gallery media records (DB only, S3 untouched)")


if __name__ == "__main__":
    asyncio.run(main())
