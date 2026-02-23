import argparse
import uvicorn
from api.routes import create_app


def main():
    parser = argparse.ArgumentParser(description="Bolchai Engine")
    parser.add_argument("--port", type=int, default=39821)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
