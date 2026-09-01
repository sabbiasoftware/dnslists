from enum import Enum, auto
import subprocess
import os
import time


class DomainType(Enum):
    WHITE = (auto(),)
    BLACK = (auto(),)
    UNKNOWN = auto()


def is_match(domain, domains):
    if domain in domains:
        return True

    for i in range(0, len(domain)):
        if "@@||{}^".format(domain[i:]) in domains:
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


def readDomains(verbose=False):
    start = time.time()

    def elapsed():
        return time.time() - start

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
        if verbose:
            print(f"readDomains took {elapsed():.3f}s")
        return []

    select_nonhu = select.format(lookback, "not ")
    domains_nonhu = runQuery(select_nonhu)
    if domains_nonhu is None:
        if verbose:
            print(f"readDomains took {elapsed():.3f}s")
        return []

    if verbose:
        print(f"readDomains took {elapsed():.3f}s")
    return domains_hu + domains_nonhu


def readDomains2(verbose=False):
    start = time.time()

    lookback = "28 day"
    mintimestamp = time.time() - 28 * 24 * 60 * 60

    select = f"""
        select distinct d.domain
        from query_storage q
        inner join client_by_id c on q.client = c.id
        inner join domain_by_id d on q.domain = d.id
        where
            (c.ip='192.168.1.103' or c.ip='192.168.1.101' or c.ip='192.168.1.154') and
            status in (1, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 18) and
            timestamp >= {mintimestamp}
    """
    domains = runQuery(select)
    if verbose:
        delta = time.time() - start
        print(f"readDomains took {delta:.3f}s")
    return domains


def filterDomains(domains, whitelist, blacklist, verbose=False):
    start = time.time()

    whitelistset = set(whitelist)
    blacklistset = set(blacklist)

    result = list(
        filter(
            lambda d: (d != "")
            and not is_match(d, whitelistset)
            and not is_match(d, blacklistset),
            domains,
        )
    )
    if verbose:
        print(f"filterDomains took {time.time() - start:.3f}s")
    return result
