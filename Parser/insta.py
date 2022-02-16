from instascrape import Profile

profile = Profile('https://www.instagram.com/andrey_kortosov/')

cocks = '34570232%3Aak0k6C0C8VX4ze%3A23'
header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/94.0.4606.85 YaBrowser/21.11.4.727 Yowser/2.5 Safari/537.36",
    "cookie": f"sessionid={cocks}"
}

profile.scrape(headers=header)

print(profile)
