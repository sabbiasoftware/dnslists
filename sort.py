import subprocess

queryres = subprocess.run(
    'sudo sqlite3 /etc/pihole/pihole-FTL.db "select distinct domain from queries order by timestamp desc limit 32"',
    shell=True,
    capture_output=True,
)
domains = queryres.stdout.decode("utf-8").split("\n")
for domain in domains:
    checkres = subprocess.run(
        "sudo pihole -q {}".format(domain), shell=True, capture_output=True
    )
    checkresout = checkres.stdout.decode("utf-8")
    is_white = checkresout.find("whitelist")
    is_black = checkresout.find("blacklist")

    print("{}{} {}", "W" if is_white else " ", "B" if is_black else " ", domain)
