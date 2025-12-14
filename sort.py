import os
import sys
import subprocess
import curses

exitNeeded = False
exitCode = 0
exitMessage = ""


def needExit(code, message):
    global exitNeeded, exitCode, exitMessage

    exitNeeded = True
    exitCode = code
    exitMessage = message


def is_match(domain, list):
    if domain in list:
        return True

    for i in range(0, len(domain)):
        if "@@||{}^".format(domain[i:]) in list:
            return True
    return False


def readList(listfilename):
    list = []
    with open(listfilename, "r") as f:
        list = f.read().splitlines()
    return list


def writeList(listfilename, list):
    with open(listfilename, "w") as f:
        f.write("\n".join(list) + "\n")


def addToList(domain, listfilename):
    with open(listfilename, "a+") as f:
        f.seek(0, 2)
        trailingNewLine = f.read() == "\n"
        f.seek(0, 2)
        if not trailingNewLine:
            f.write("\n")
        f.write(domain)
        f.write("\n")


def readDomains():
    dbfns = ["pihole-FTL.db", "/etc/pihole/pihole-FTL.db"]
    dbfn = None
    for fn in dbfns:
        if os.path.isfile(fn):
            dbfn = fn
            break

    if dbfn is None:
        needExit(1, "Could not find database")
        return None

    queryres = subprocess.run(
        "sudo sqlite3 {} "
        '"select '
        "  domain "
        "from queries "
        "where "
        "  (client='192.168.1.103' or client='192.168.1.101') and "
        "  status in (1, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 18) and "
        "  datetime(timestamp, 'unixepoch', 'localtime') > datetime('now', '-1 day') "
        "group by domain "
        "order by count(id) desc "
        'limit 80"'.format(dbfn),
        shell=True,
        capture_output=True,
    )
    if queryres.returncode != 0:
        needExit(
            1, "Error when attempting to run query:\n" + queryres.stderr.decode("utf-8")
        )
        return None
    else:
        return queryres.stdout.decode("utf-8").split("\n")


def main(stdscr):
    global exitNeeded

    curses.curs_set(False)
    whitelist = readList("whitelist")
    blacklist = readList("blacklist")
    domains = readDomains()

    if domains is None or exitNeeded:
        return

    domains = list(
        filter(
            lambda d: (d != "")
            and not is_match(d, whitelist)
            and not is_match(d, blacklist),
            domains,
        )
    )

    if len(domains) == 0:
        needExit(0, "No domains to sort")
        return

    di = 0
    while True:
        # "sudo pihole -q {}".format(domain), shell=True, capture_output=True
        domain = domains[di]

        is_white = is_match(domain, whitelist)
        is_black = is_match(domain, blacklist)
        is_listed = is_white or is_black

        i = 0
        while True:
            stdscr.addstr(
                "{} / {}   {}{}   {} [{}]".format(
                    di + 1,
                    len(domains),
                    "W" if is_white else "_",
                    "B" if is_black else "_",
                    domain,
                    domain[i:],
                )
            )
            stdscr.addstr("\n[q] quit   [s] save   [jk] prev/next")
            stdscr.addstr(
                "   [hl] slice   [b] black   [w] white   [B] black-ABP   [W] white-ABP"
                if not is_listed
                else "                                                                     "
            )
            stdscr.move(0, 0)
            stdscr.refresh()
            c = stdscr.getkey()
            if c == "q":
                exit(0)
            elif c == "s":
                writeList("whitelist", whitelist)
                writeList("blacklist", blacklist)
            elif c == "j":
                di = (di + 1) % len(domains)
                break
            elif c == "k":
                di = (di - 1) % len(domains)
                break
            elif not is_listed:
                if c in "bwBW":
                    domainToAdd = (
                        domain[i:] if c in "bw" else "@@||{}^".format(domain[i:])
                    )
                    listToAdd = whitelist if c in "wW" else blacklist
                    listToAdd.append(domainToAdd)
                    di = (di + 1) % len(domains)
                    break
                elif c == "h":
                    i = max(0, i - 1)
                elif c == "l":
                    i = min(i + 1, len(domain))

        # print("{}{} {}".format("W" if is_white else " ", "B" if is_black else " ", domain))


curses.wrapper(main)
if exitMessage != "":
    print(exitMessage)
sys.exit(exitCode)
