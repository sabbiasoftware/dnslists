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


def checkIntersection(l1, l2):
    intersection = list(set(whitelist) & set(blacklist))
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
