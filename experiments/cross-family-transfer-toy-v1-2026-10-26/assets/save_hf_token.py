"""User-run, hidden-input login helper for the separately authorized HF account."""
import getpass
import os
from pathlib import Path
import sys
import warnings


def main():
    target = Path("/workspace/hf_ruizhixu/token")
    if not sys.stdin.isatty():
        raise SystemExit("A terminal is required. Run this helper with ssh -t.")
    if target.exists() or target.is_symlink():
        raise SystemExit(f"Refusing to overwrite existing credential: {target}")
    print("Enter only a read token from the approved Hugging Face account RuizhiXu.")
    print("Input is hidden. Do not paste the token into chat.")
    warnings.simplefilter("error", getpass.GetPassWarning)
    token = getpass.getpass("RuizhiXu HF token (hidden): ").strip()
    if not token.startswith("hf_") or any(char.isspace() for char in token):
        raise SystemExit("Invalid token format; nothing was saved.")
    os.umask(0o077)
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    target.parent.chmod(0o700)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(token + "\n")
    print(f"Saved to {target} with mode 600. Account and access still require verification.")


if __name__ == "__main__":
    main()
