import subprocess

queryres = subprocess.run(
    'sudo sqlite3 /etc/pihole/pihole-FTL.db "select distinct domain from queries order by timestamp desc limit 32"'
)
domains = queryres.stdout.decode("utf-8").split("\n")
for domain in domains:
    print(domain)
