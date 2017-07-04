import json
import sys

import requests
from bs4 import BeautifulSoup

def fetch_page(url):
    response = requests.get(url)
    return response


def parse_movies_list():
    url = 'http://www.the-numbers.com/movie/budgets/all'
    html = fetch_page(url).text
    soup = BeautifulSoup(html.encode('utf-8'), 'html.parser')

    parse_dollars = lambda x: int(x.replace('$', '').replace(',', ''))

    movies = soup.find_all('td')
    movies_data = []
    number_of_movies = 1000
    spaces = ' ' * 80
    for c, i in enumerate(range(0, 6*number_of_movies, 6)):
        name = movies[i+2].text.strip()
        print('{}\r'.format(spaces), end='')
        percent = c / number_of_movies * 100
        print('{} %\t{}\r'.format(percent, name), end='')
        """
        if percent % 10 == 0:
            save_data('tmp_{}.json'.format(percent), movie_data)
        """

        movie_data = {}

        movie_data['budget'] = parse_dollars(movies[i+3].text)
        movie_data['gross'] = parse_dollars(movies[i+5].text)
        movie_data.update(get_imdb_data(name))
        movies_data.append(movie_data)

    return movies_data


def get_imdb_data(name):
    url_imdb = 'http://www.imdb.com'

    # Research with name
    url = '{}/find?ref_=nv_sr_fn&q={}&s=tt'.format(url_imdb, name)
    response = fetch_page(url)
    if response.status_code != 200:
        return {}

    # Scrapping movie data
    soup = BeautifulSoup(response.text, 'html.parser')
    movie_url = soup.find('td', 'result_text').a['href']
    response = fetch_page('{}{}'.format(url_imdb, movie_url))
    if response.status_code != 200:
        return {}
    movie = parse_movie(BeautifulSoup(response.text.encode('utf-8'), 'html.parser'))

    reviews_url = '{}/title/{}/reviews?ref_=tt_urv'\
                    .format(url_imdb, movie_url.split('/')[2])
    response = fetch_page(reviews_url)
    if response.status_code != 200:
        movie.update({'reviews': []})
        return movie
    reviews = parse_reviews(BeautifulSoup(response.text.encode('utf-8'), 'html.parser'))
    movie.update({'reviews': reviews})
    return movie


def parse_reviews(soup):
    reviews = []
    for review in soup.find_all('h2'):
        data = {}
        data['title'] = review.text
        try:
            data['score'] = float(review.next.next.next['alt'].split('/')[0])
        except:
            data['score'] = .0

        data['content'] = review.parent.next_sibling.next_sibling.text
        reviews.append(data)
    return reviews


def parse_movie(soup):
    """
    This is ugly, forgive me.
    """
    movie = {}

    try:
        movie['title'] = soup.title.text[:-7]
    except:
        movie['title'] = ''

    try:
        movie['genres'] = [
                genre.text
                for genre in soup.find_all('span', attrs={'itemprop':'genre'})
     ]
    except:
        movie['genres'] = []

    try:
        movie['score'] = float(soup.find('span', attrs={'itemprop': 'ratingValue'}).text)
    except:
        movie['score'] = .0

    try:
        movie['year'] = int(soup.find('span', id='titleYear').text[1:-1])
    except:
        movie['year'] = 0

    try:
        movie['director'] = soup.find('span', attrs={'itemprop': 'director'}).text.strip()
    except:
        movie['director'] = ''

    try:
        movie['actors'] = [
                actor.text.strip().replace(',', '')
                for actor in soup.find_all('span', attrs={'itemprop': 'actors'})
        ]
    except:
        movie['actors'] = []

    return movie


def save_data(path, data):
    with open(path, 'w+') as f:
        f.write(json.dumps(data, indent=2))


if __name__ == '__main__':
    movies = parse_movies_list()
    save_data('imdb.json', movies)