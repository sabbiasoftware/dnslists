from domain_helpers import DomainType
from inspect_url import inspect_url
from inspect_content import inspect_content


def inspect_domain(domain: str) -> tuple[DomainType, str]:
    dt, msg = inspect_url(domain)
    if dt == DomainType.BLACK:
        return dt, msg
    return inspect_content(domain)
