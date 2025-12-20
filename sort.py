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


def runQuery(select):
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
        '{}sqlite3 {} "{}"'.format(
            "sudo " if not os.access(dbfn, os.R_OK) else "", dbfn, select
        ),
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


def readDomains():
    select = """
        select
          domain
        from queries
        where
          (client='192.168.1.103' or client='192.168.1.101' or client='192.168.1.102') and
          status in (1, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 18) and
          datetime(timestamp, 'unixepoch', 'localtime') > datetime('now', '-28 day') and
          domain like '%.hu'
        group by domain
        order by count(id)
    """

    domains = runQuery(select)
    if domains is None:
        return

    select = """
        select
          domain
        from queries
        where
          (client='192.168.1.103' or client='192.168.1.101' or client='192.168.1.102') and
          status in (1, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 18) and
          datetime(timestamp, 'unixepoch', 'localtime') > datetime('now', '-28 day') and
          domain not like '%.hu'
        group by domain
        order by count(id)
    """

    domains2 = runQuery(select)
    if domains2 is None:
        return

    return domains + domains2


def checkDomain(domain):
    cmd = "rg -m 4 {} lists".format(domain)
    checkres = subprocess.run(cmd, shell=True, capture_output=True)
    if checkres.returncode != 0:
        return ""  # checkres.stderr.decode("utf-8")
    else:
        return checkres.stdout.decode("utf-8")


def main(stdscr):
    global exitNeeded

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

    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)

    di = 0
    while True:
        # "sudo pihole -q {}".format(domain), shell=True, capture_output=True
        domain = domains[di]

        is_white = is_match(domain, whitelist)
        is_black = is_match(domain, blacklist)
        is_listed = is_white or is_black

        i = 0
        info = ""
        while True:
            stdscr.clear()
            stdscr.addstr(
                0,
                0,
                "{} / {}   {}{}   {} [{}]".format(
                    di + 1,
                    len(domains),
                    "W" if is_white else "_",
                    "B" if is_black else "_",
                    domain,
                    domain[i:],
                ),
                curses.color_pair(
                    2
                    if is_black and not is_white
                    else (3 if is_white and not is_black else 4)
                ),
            )
            stdscr.addstr(
                1,
                0,
                "[q] quit   [s] save   [jk] prev/next   [hl] slice   [c] check   [C] check all",
            )
            if not is_listed:
                stdscr.addstr(
                    2,
                    0,
                    "[b] black   [w] white   [B] black-ABP   [W] white-ABP",
                )
            stdscr.addstr(4, 0, info)
            stdscr.refresh()

            c = stdscr.getkey()

            if c == "q":
                exit(0)
            elif c == "s":
                writeList("whitelist", whitelist)
                writeList("blacklist", blacklist)
                info = "Lists saved"
            elif c == "j":
                di = (di + 1) % len(domains)
                info = ""
                break
            elif c == "k":
                di = (di - 1) % len(domains)
                info = ""
                break
            elif c == "h":
                i = max(0, i - 1)
            elif c == "l":
                i = min(i + 1, len(domain))
            elif c == "c":
                checkres = checkDomain(domain[i:])
                info = checkres
            elif c == "C":
                for d in domains:
                    stdscr.addstr(4, 0, "Checking: " + d)
                    stdscr.clrtoeol()
                    stdscr.refresh()
                    if checkDomain(d) != "":
                        blacklist.append(d)
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

        # print("{}{} {}".format("W" if is_white else " ", "B" if is_black else " ", domain))


curses.wrapper(main)
if exitMessage != "":
    print(exitMessage)
sys.exit(exitCode)
