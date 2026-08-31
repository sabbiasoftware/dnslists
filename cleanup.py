from domain_helpers import readList, writeList


def checkIntersection(l1, l2):
    intersection = list(set(l1) & set(l2))
    if len(intersection) > 0:
        print("In both lists:")
        for i in intersection:
            print(i)


def checkRedundancy(l1):
    redundancy = []
    toremove = set()
    for d in l1:
        if not d.startswith("@"):
            continue
        dd = d[4:-1]

        for e in l1:
            if e.endswith("." + dd):
                redundancy.append("{} redundant due to {}".format(e, d))
                toremove.add(e)

    if len(redundancy) > 0:
        print("redundancies found:")
        print(redundancy, sep="\n")

    for r in toremove:
        l1.remove(r)


whitelist = readList("whitelist")
blacklist = readList("blacklist")

checkIntersection(whitelist, blacklist)

checkRedundancy(whitelist)
writeList("whitelist", whitelist)

checkRedundancy(blacklist)
writeList("blacklist", blacklist)
