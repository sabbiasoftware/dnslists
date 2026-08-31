from enum import Enum, auto
import subprocess
import os


class DomainType(Enum):
    WHITE = (auto(),)
    BLACK = (auto(),)
    UNKNOWN = auto()


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


def runQuery(select):
    dbfns = ["pihole-FTL.db", "/etc/pihole/pihole-FTL.db"]
    dbfn = None
    for fn in dbfns:
        if os.path.isfile(fn):
            dbfn = fn
            break

    if dbfn is None:
        print("Could not find database")
        return []

    queryres = subprocess.run(
        '{}sqlite3 {} "{}"'.format(
            "sudo " if not os.access(dbfn, os.R_OK) else "", dbfn, select
        ),
        shell=True,
        capture_output=True,
    )
    if queryres.returncode != 0:
        print("Error when attempting to run query:\n" + queryres.stderr.decode("utf-8"))
        return []
    else:
        return queryres.stdout.decode("utf-8").split("\n")


def readDomains():
    lookback = "28 day"

    select = """
        select
          domain
        from queries
        where
          (client='192.168.1.103' or client='192.168.1.101' or client='192.168.1.154') and
          status in (1, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 18) and
          datetime(timestamp, 'unixepoch', 'localtime') > datetime('now', '-{}') and
          domain {}like '%.hu'
        group by domain
        order by count(id)
    """

    select_hu = select.format(lookback, "")
    domains_hu = runQuery(select_hu)
    if domains_hu is None:
        return []

    select_nonhu = select.format(lookback, "not ")
    domains_nonhu = runQuery(select_nonhu)
    if domains_nonhu is None:
        return []

    return domains_hu + domains_nonhu


def filterDomains(domains, whitelist, blacklist):
    return list(
        filter(
            lambda d: (d != "")
            and not is_match(d, whitelist)
            and not is_match(d, blacklist),
            domains,
        )
    )
