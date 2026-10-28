"""Exec a configured child with an address-space limit, without preexec_fn."""
import os
import sys


def main():
    limit = int(sys.argv[1])
    if limit:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    target = sys.argv[2]
    args = sys.argv[2:]
    if sys.platform == "win32":
        try:
            with open(target, "rb") as f:
                header = f.read(256)
            if header.startswith(b"#!"):
                shebang = header.split(b"\n")[0][2:].decode().strip()
                target = shebang
                args = [shebang, sys.argv[2]] + sys.argv[3:]
        except OSError:
            pass
    os.execv(target, args)


if __name__ == "__main__":
    main()
