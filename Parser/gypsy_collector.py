import instaloader
import configparser
from tqdm import tqdm

sorts_of_shit = ["астролог", "нумеролог", "оккультизм", "экстрасенсорика",
                 "космоэнергетика", "биоэнергетика", "ясновидение", "рэйки",
                 "гадания", "хиромантия", "спиритизм", "целительство",
                 "каббала", "парапсихология", "трансерфинг", "ченнелер",
                 "дизайн человека", "осознанные сновидения", "контактер",
                 "тетахилинг", "гипнолог", "регрессолог", "коуч", "мотиватор",
                 "руны", "веды", "аюрведа", "проводник", "сексолог", "расстановки по хеллингеру"]

config = configparser.ConfigParser()
config.read("settings.ini")
user = config.get('instagram', 'user')
password = config.get('instagram', 'password')

insta_session = instaloader.Instaloader()  # Get instance of instagram
insta_session.login(user, password)


def users_from_word(topic: str, stats: dict):
    """
    Collect popular users, save them to txt.
    Plus collect stats on each topic.
    :param topic: search words or hashtag in instagram
    :param stats: dict
    :return: Update to gypsy_list.txt and stats.json
    """

    searcher = instaloader.TopSearchResults(insta_session.context, topic)

    leaders = []
    followers_sum = 0
    posts_sum = 0
    leader_count = 0
    for i, gypsy in enumerate(searcher.get_profiles()):
        if (gypsy.followers > 25000) & (gypsy.mediacount > 200) & (not gypsy.is_private):
            leaders.append(gypsy.username)
            leader_count += 1

        followers_sum += gypsy.followers
        posts_sum += gypsy.mediacount

        if i > 18:
            break

    stats.update({topic: {'followers': followers_sum, 'posts': posts_sum}})

    with open("gypsy_leaderboard.txt", "a", encoding="utf-8") as file:
        file.writelines(f'{topic} {followers_sum} {posts_sum} {leader_count} \n')
        # json.dump(stats, file)

    with open("gypsy_list.txt", "a", encoding="utf-8") as file:
        file.writelines(['\n'.join(leaders), '\n'])


stats = {}
for topic in tqdm(sorts_of_shit):
    # print(topic)
    users_from_word(topic, stats)

