import argparse
import datetime
import fcntl
import os
import sys
import time

from domain_helpers import DomainType, readDomains2, readList, writeList, filterDomains
from inspect_domain import inspect_domain

logts = None


def startlog():
    global logts
    logts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def log(msg: str):
    global logts
    if logts is None:
        startlog()
    print(f"{logts} {msg}")
    logts = None


def main():
    parser = argparse.ArgumentParser(
        description="Automatically sort domains into blacklist/whitelist"
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update lists automatically (default: dry-run)",
    )
    args = parser.parse_args()
    dry_run = not args.update

    lock_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "autosort.lock"
    )
    try:
        lock_fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT, 0o644)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Another instance is running, exiting.")
        sys.exit(0)

    startlog()
    start = time.time()

    whitelist = readList("whitelist")
    blacklist = readList("blacklist")
    domains = filterDomains(
        readDomains2(verbose=False), whitelist, blacklist, verbose=False
    )

    whiteChanged = False
    blackChanged = False

    sorted_count = 0
    if domains and len(domains) > 0:
        log("Autosort: begin sorting")
        for domain in domains:
            sorted_count += 1
            try:
                domain_type, msg = inspect_domain(domain)
            except Exception as e:
                domain_type = DomainType.UNKNOWN
                msg = f"Error: {e}"

            log(f"{domain_type.name} {domain} ({msg})")

            if not dry_run:
                if domain_type == DomainType.BLACK:
                    blacklist.append(domain)
                    blackChanged = True
                elif domain_type == DomainType.WHITE:
                    whitelist.append(domain)
                    whiteChanged = True

        if not dry_run:
            if whiteChanged:
                writeList("whitelist", whitelist)
            if blackChanged:
                writeList("blacklist", blacklist)

        log(f"Autosort: sorted {sorted_count} domains ({time.time() - start:.3f}s)")
    else:
        global logts
        logts = None
        log(f"Autosort: no domains ({time.time() - start:.3f}s)")

    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)


if __name__ == "__main__":
    main()
