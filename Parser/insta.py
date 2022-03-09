import instaloader
import requests
import random
from PIL import Image
from tqdm import tqdm
import os
import re
from queue import Queue
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'


class Agent(instaloader.Instaloader):
    """
    Extended instaloader class with username(str)
    to catch baned accounts from agents list in settings.ini
    """
    def __init__(self, **args):
        super().__init__(**args)
        self.username = ''

    def login(self, user, password):
        super().login(user, password)
        self.username = user


def get_agents(agents_count=9999):
    """
    Returns Queue of instagram sessions objects from different users
    """
    with open('settings.ini', 'r') as config:
        data = config.readlines()
        random.shuffle(data)
        agents = Queue()
        agents_in_action = 0
        first_fail = []

        for line in tqdm(data):
            user, password = line.split()
            try:
                insta_session = Agent(max_connection_attempts=6, request_timeout=1000.0)
                insta_session.login(user, password)
                agents.put(insta_session)
                agents_in_action += 1
                if agents_in_action >= agents_count:
                    break
            except instaloader.exceptions.ConnectionException:
                first_fail.append((user, password))
                continue
        print(f'{agents_count} agents are ready to PARSE!')

        second_fail = []
        if agents_count > 50:
            for loser in tqdm(first_fail):
                user, password = loser
                try:
                    insta_session = Agent(max_connection_attempts=6, request_timeout=1000.0)
                    insta_session.login(user, password)
                    agents.put(insta_session)
                    agents_in_action += 1
                except instaloader.exceptions.ConnectionException:
                    second_fail.append((user, password))
                    continue
            print(f'{agents_in_action} active agents out of {len(data)}\n'
                  f'{len(second_fail)} are still lazy bastards')

    return agents


def change_agent(agents: Queue):
    """
    Login into next account from queue and puts in the back
    """
    agent_session = agents.get()
    agents.put(agent_session)
    return agent_session


def get_text_from_image(url: str):
    """
    Convert image to text by OCR processing.

    url: str
        link to source

    Return (str) text from image
    """
    img = Image.open(requests.get(url, stream=True).raw)
    text = pytesseract.image_to_string(img, lang='rus')
    return str(text)


def get_metrics(text: str):
    '''
    Calculate basic metrics such as
    amount of symbols,
    amount of words and
    average length of a word.

    text: str
        an
    Return [str, str, str] basic metrics
    '''

    symbols = len(text)
    words = len(text.split())
    avg_word_len = symbols // words
    return symbols, words, avg_word_len


def get_filename(username: str):
    return re.sub(r'\W', '_', username)


def get_posts_list(username: str, instance):
    """
    Collect shortcodes of all posts in account.
    Works once with the first run, then reads shortcodes from file/

    username: str
        @username from instagram
    instance: instaloader object
        object of opened session

    Return (list) post labels.
    """

    file_name = get_filename(username)

    if os.path.exists(f'data/{file_name}.txt'):
        if os.path.exists(f'data/task_{file_name}.txt'):
            with open(f'data/task_{file_name}.txt', 'r', encoding='utf-8') as file:
                posts = file.read().split()
            print('Read task from file')
        else:
            posts = []  # Parsing was done earlier
            print('Job is done')
    else:
        insta_diva = instaloader.Profile.from_username(instance.context, username)  # create object of account
        posts = []  # collecting posts shortcodes
        posts_count = 0
        for post in tqdm(insta_diva.get_posts()):
            posts.append(post.shortcode)
            posts_count += 1
            if posts_count > 2000:  # It's enough for one person (Just because!)
                break

        with open(f'data/task_{file_name}.txt', 'w', encoding='utf-8') as file:
            file.write(' '.join(posts))
        print('Task file created')

    return posts


def get_all_text(post: str, instance):
    """
    Collects texts from post caption, images in carousel
    and owner's comments.

    post: str
        shortcode of a post
    instance: instaloader object
        object of opened session

    Returns (str) combined post text.
        """
    insta_post = instaloader.Post.from_shortcode(instance.context, post)  # post object

    post_text = insta_post.caption  # Short captions are useless

    if not post_text:
        return ''

    if len(post_text) < 1000:
        return ''

    carousel_text = ''  # parse text from all images in carousel
    if insta_post.mediacount > 1:
        for i, carousel in enumerate(insta_post.get_sidecar_nodes()):  # Get all pics from carousel
            if i == 0:
                continue
            url = carousel.display_url
            image_text = get_text_from_image(url)
            image_text = re.sub(r'\n', ' ', image_text)
            if image_text:
                symbols, words, avg_word_len = get_metrics(image_text)
                if (words > 20) & (avg_word_len > 4):
                    carousel_text += image_text + ' '

    comments_text = ''  # parse first owner's comments
    for comment in insta_post.get_comments():
        if comment.owner.username == insta_post.owner_username:
            comments_text += comment.text
            continue
        break

    total_text = post_text + '\n\n' + carousel_text + comments_text + '\n\n\n\n'

    return total_text


def update_task_file(done_posts: list, file_name: str):
    """
    Delete collected posts from task file.

    done_posts: list
        list of shortcodes
    file_name: str

    Updates task file.
    """
    with open(f'data/task_{file_name}.txt', 'r', encoding='utf-8') as file:
        posts = file.read().split()

    for post in done_posts:
        try:
            del posts[posts.index(post)]
        except Exception as ex:
            print('Post doesnt exist in task file')
            print(ex)

    if posts:
        with open(f'data/task_{file_name}.txt', 'w', encoding='utf-8') as file:
            file.write(' '.join(posts))
    else:
        os.remove(f'data/task_{file_name}.txt')


def gypsy_parse(username: str):
    '''
    Parse all posts from instagram @username and collect them
    in username.txt file

    :param username: str
    :return: txt file
    '''
    agents = get_agents(20)

    insta_session = change_agent(agents)  # Get instance of instagram

    gypsy_name = username
    file_name = get_filename(gypsy_name)

    gypsy_posts = get_posts_list(gypsy_name, insta_session)
    done_posts = []
    agent_activity = 0
    
    for post in tqdm(gypsy_posts):
        try:
            full_post = get_all_text(post, insta_session)
            if full_post:
                with open(f'data/{file_name}.txt', 'a', encoding='utf-8') as file:
                    file.write('<STARTOFPOST> ')
                    file.write(full_post)

            agent_activity += 1
            if agent_activity > 1:
                agent_activity = 0
                insta_session = change_agent(agents)

            done_posts.append(post)

        except instaloader.exceptions.TooManyRequestsException:
            print(f'Too many requests from: {insta_session.username}')
            insta_session = change_agent(agents)
            continue
        except instaloader.exceptions.QueryReturnedBadRequestException:
            print(f'Bad request from: {insta_session.username}')
            insta_session = change_agent(agents)
            continue
        except requests.exceptions.ConnectionError:
            print('Connection aborted')
            insta_session = change_agent(agents)
            continue
        except Exception as ex:
            print(ex)
            break

    update_task_file(done_posts, file_name)


if __name__ == "__main__":
    gypsy_parse('transerfing_center')
