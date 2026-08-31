from hashlib import blake2b
import sys
import locale
import curses
from wcwidth import wcwidth
from domain_helpers import (
    DomainType,
    readList,
    writeList,
    readDomains,
    filterDomains,
    is_match,
)
from inspect_url import inspect_url
from inspect_content import inspect_content
from inspect_domain import inspect_domain


def setUnicodeLocale():
    try:
        locale.setlocale(locale.LC_ALL, "")
        return
    except locale.Error:
        pass

    for name in ("hu_HU.UTF-8", "C.UTF-8", "en_US.UTF-8"):
        try:
            locale.setlocale(locale.LC_ALL, name)
            return
        except locale.Error:
            continue


setUnicodeLocale()


def addstrClip(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    maxcol = w - x
    for i, line in enumerate(text.splitlines()):
        if y + i >= h:
            break
        if maxcol <= 0:
            return
        col = 0
        end = len(line)
        for j, ch in enumerate(line):
            width = wcwidth(ch) if 1 < len(ch.encode("utf-8")) else 1
            if width == -1:
                width = 1
            if col + width > maxcol:
                end = j
                break
            col += width
        stdscr.addstr(y + i, x, line[:end], attr)


whitelist = readList("whitelist")
blacklist = readList("blacklist")
# domains = readDomains()
domains = filterDomains(readDomains(), whitelist, blacklist)


def main(stdscr):
    global whiteList
    global blacklist
    global domains

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
            addstrClip(
                stdscr,
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
            addstrClip(
                stdscr,
                1,
                0,
                "[q] quit   [s] save   [jk] prev/next   [hl] slice   [c] check   [C] check all   [i] inspect",
            )
            if not is_listed:
                addstrClip(
                    stdscr,
                    2,
                    0,
                    "[b] black   [w] white   [B] black-ABP   [W] white-ABP",
                )
            addstrClip(stdscr, 4, 0, info)
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
                checkres = inspect_url(domain[i:])
                info = checkres
            elif c == "C":
                for d in domains:
                    addstrClip(stdscr, 4, 0, "Checking: " + d)
                    stdscr.clrtoeol()
                    stdscr.refresh()
                    if inspect_url(d) != "":
                        blacklist.append(d)
                break
            elif c == "i":
                addstrClip(stdscr, 4, 0, "Inspecting")
                stdscr.clrtoeol()
                stdscr.refresh()
                dt, msg = inspect_domain(domain)
                if dt == DomainType.WHITE:
                    whitelist.append(domain)
                elif dt == DomainType.BLACK:
                    blacklist.append(domain)
                info = msg
            if c in "bwBW":
                domainToToggle = (
                    domain[i:] if c in "bw" else "@@||{}^".format(domain[i:])
                )
                listToToggle = whitelist if c in "wW" else blacklist
                if domainToToggle in listToToggle:
                    listToToggle.remove(domainToToggle)
                else:
                    listToToggle.append(domainToToggle)
                # di = (di + 1) % len(domains)
                break

        # print("{}{} {}".format("W" if is_white else " ", "B" if is_black else " ", domain))


if len(domains) == 0:
    print("No domains to sort")
    sys.exit(0)

curses.wrapper(main)
