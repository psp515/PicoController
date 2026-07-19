import sys

if "lib" not in sys.path:
    sys.path.append("lib")

import asyncio


async def main():
    pass


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
finally:
    asyncio.new_event_loop()
