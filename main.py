import sys

if "lib" not in sys.path:
    sys.path.append("lib")
if "src" not in sys.path:
    sys.path.append("src")

import asyncio

from application import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.new_event_loop()
