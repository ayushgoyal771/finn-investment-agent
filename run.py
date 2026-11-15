"""python run.py [--host 127.0.0.1] [--port 8000]"""
import argparse
import os

from dotenv import load_dotenv
import uvicorn

if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run FINN locally")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=os.getenv("PORT", "8000"))
    args = parser.parse_args()
    public_demo = os.getenv("FINN_PUBLIC_DEMO", "false").lower() == "true"
    if args.host not in {"127.0.0.1", "localhost", "::1"} and not os.getenv("FINN_ACCESS_TOKEN") and not public_demo:
        parser.error("Set FINN_ACCESS_TOKEN before allowing remote connections. See README.md.")
    uvicorn.run("backend.main:app", host=args.host, port=args.port, log_level="info")
