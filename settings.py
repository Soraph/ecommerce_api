from os.path import join, dirname
from dotenv import load_dotenv
import os
import sys

# Need comment for these 2 lines from dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


def get_or_die(env, variable):
    # Will replace current lines between 18 and 22
    pass


ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

if ENVIRONMENT == 'production':
    if 'CLOUDINARY_URL' in os.environ:
        CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
    else:
        sys.exit('Missing CLOUDINARY_URL definition, quitting.')
