import subprocess
from domain_helpers import DomainType, readList


def inspect_url(domain: str) -> tuple[DomainType, str]:
    blackEnd = readList("blacklist_urlkeywords")
    for be in blackEnd:
        if domain.endswith(be):
            return DomainType.BLACK, "Black end: " + be

    cmd = 'rg -m 4 " {}\\$" lists'.format(domain)
    checkres = subprocess.run(cmd, shell=True, capture_output=True)
    if checkres.returncode == 0:
        return DomainType.BLACK, "Found in lists"

    return DomainType.WHITE, ""
