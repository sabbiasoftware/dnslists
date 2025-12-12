import subprocess

queryres = subprocess.run(
    "sudo sqlite3 /etc/pihole/pihole-FTL.db "
    '"select '
    "  domain "
    "from queries "
    "where "
    "  (client='192.168.1.103' or client='192.168.1.101') and "
    "  status in (1, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 18) and "
    "  datetime(timestamp, 'unixepoch', 'localtime') > datetime('now', '-3 day') "
    "group by domain "
    "order by count(id) desc "
    'limit 80"',
    shell=True,
    capture_output=True,
)
if queryres.returncode != 0:
    print("Error when attempting to run query:")
    print(queryres.stderr.decode("utf-8"))
    exit(1)

domains = queryres.stdout.decode("utf-8").split("\n")
print("Found {} domains".format(len(domains)))
for domain in domains:
    checkres = subprocess.run(
        "sudo pihole -q {}".format(domain), shell=True, capture_output=True
    )
    checkresout = checkres.stdout.decode("utf-8")
    is_white = checkresout.find("whitelist") != -1
    is_black = checkresout.find("blacklist") != -1

    print("{}{} {}".format("W" if is_white else " ", "B" if is_black else " ", domain))
