"""Exec a configured child with an address-space limit, without preexec_fn."""
import os
import sys


def main():
    limit = int(sys.argv[1])
    if limit:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    os.execv(sys.argv[2], sys.argv[2:])


if __name__ == "__main__":
    main()
