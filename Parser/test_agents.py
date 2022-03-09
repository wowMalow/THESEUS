"""
Script for testing parsing ability of instagram-accounts
from settings.ini
"""
import instaloader
import insta as utility


agents = utility.get_agents()

post = 'B_r6t8VJBqi'  # Random post

while not agents.empty():
    agent = agents.get()
    try:
        insta_post = instaloader.Post.from_shortcode(agent.context, post)
    except instaloader.exceptions.QueryReturnedBadRequestException:
        print(agent.username)
    except Exception as ex:
        print(ex)
