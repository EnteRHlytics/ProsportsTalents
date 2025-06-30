import os
import shutil
import sys


def check_storage(path: str, required_mb: int = 100) -> int:
    if not os.path.exists(path):
        print(f"Path {path} does not exist", file=sys.stderr)
        return 1

    total, used, free = shutil.disk_usage(path)
    free_mb = free / (1024 * 1024)

    if free_mb < required_mb:
        print(
            f"Insufficient space in {path}: {free_mb:.2f} MB free, "
            f"{required_mb} MB required",
            file=sys.stderr,
        )
        return 1

    print(f"{path} has sufficient space: {free_mb:.2f} MB free")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    required = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    sys.exit(check_storage(path, required))
