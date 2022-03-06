import instaloader
import requests
from PIL import Image
from tqdm import tqdm
import os
import configparser
import re
from queue import Queue
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract\tesseract.exe'


def change_agent(agents):
    acting_agent = agents.get()
    agents.put(acting_agent)
    return acting_agent


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
            if posts_count > 1500:  # It's enough for one person (Just because!)
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


def gypsy_parse(username: str, start=0):
    '''
    Parse all posts from instagram @username and collect them
    in username.txt file

    :param username: str
    :return: txt file
    '''
    config = configparser.ConfigParser()
    config.read("settings.ini")
    user = config.get('instagram', 'user')
    password = config.get('instagram', 'password')

    insta_session = instaloader.Instaloader()  # Get instance of instagram
    insta_session.login(user, password)

    gypsy_name = username
    file_name = get_filename(gypsy_name)

    gypsy_posts = get_posts_list(gypsy_name, insta_session)
    done_posts = []
    for post in tqdm(gypsy_posts[start:]):
        try:
            full_post = get_all_text(post, insta_session)
            if full_post:
                with open(f'data/{file_name}.txt', 'a', encoding='utf-8') as file:
                    file.write('<STARTOFPOST> ')
                    file.write(full_post)

            done_posts.append(post)

        except Exception as ex:
            print(ex)
            break

    update_task_file(done_posts, file_name)


if __name__ == "__main__":
    gypsy_parse('natasha_astrolog')
