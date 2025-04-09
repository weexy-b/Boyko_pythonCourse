import requests
import csv
from datetime import datetime, timedelta
from collections import defaultdict, namedtuple


class MovieDataProcessor:
    def __init__(self, num_pages):
        self.num_pages = num_pages
        self.headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMTI3NGFmYTRlNTUyMjRjYzRlN2Q0NmNlMTNkOTZjOSIsInN1YiI6IjVkNmZhMWZmNzdjMDFmMDAxMDU5NzQ4OSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.lbpgyXlOXwrbY0mUmP-zQpNAMCw_h-oaudAJB6Cn5c8"
        }
        self.base_url = "https://api.themoviedb.org/3"
        self.movie_data = []
        self.genres = {}
        self._fetch_genres()
        self._fetch_movie_data()

    def _fetch_genres(self):
        url = f"{self.base_url}/genre/movie/list?language=en"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            genres_data = response.json()
            self.genres = {g['id']: g['name'] for g in genres_data['genres']}

    def _fetch_movie_data(self):
        for page in range(1, self.num_pages + 1):
            url = f"{self.base_url}/discover/movie?include_adult=false&include_video=false&sort_by=popularity.desc&page={page}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                page_data = response.json()
                self.movie_data.extend(page_data['results'])

    def get_all_data(self):
        return self.movie_data

    def get_sliced_data(self):
        return self.movie_data[3:19:4]

    def get_most_popular_title(self):
        if not self.movie_data:
            return None
        return max(self.movie_data, key=lambda x: x['popularity'])['title']

    def search_titles_by_keywords(self, *keywords):
        result = []
        for movie in self.movie_data:
            overview = movie.get('overview', '').lower()
            if all(keyword.lower() in overview for keyword in keywords):
                result.append(movie['title'])
        return result

    def get_unique_genres(self):
        unique_genres = set()
        for movie in self.movie_data:
            for genre_id in movie.get('genre_ids', []):
                if genre_id in self.genres:
                    unique_genres.add(self.genres[genre_id])
        return frozenset(unique_genres)

    def delete_movies_by_genre(self, genre_name):
        # Find genre ID by name
        genre_id = None
        for g_id, name in self.genres.items():
            if name.lower() == genre_name.lower():
                genre_id = g_id
                break

        if genre_id is not None:
            self.movie_data = [movie for movie in self.movie_data
                               if genre_id not in movie.get('genre_ids', [])]

    def get_most_popular_genres(self):
        genre_counts = defaultdict(int)
        for movie in self.movie_data:
            for genre_id in movie.get('genre_ids', []):
                if genre_id in self.genres:
                    genre_counts[self.genres[genre_id]] += 1

        return sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)

    def get_movies_grouped_by_genres(self):
        genre_to_movies = defaultdict(set)
        for movie in self.movie_data:
            for genre_id in movie.get('genre_ids', []):
                if genre_id in self.genres:
                    genre_to_movies[self.genres[genre_id]].add(movie['title'])

        # Convert to frozenset to make it immutable
        return {genre: frozenset(movies) for genre, movies in genre_to_movies.items()}

    def get_modified_data(self):
        modified_data = []
        for movie in self.movie_data:
            movie_copy = movie.copy()
            if 'genre_ids' in movie_copy and len(movie_copy['genre_ids']) > 0:
                movie_copy['genre_ids'] = [22] + movie_copy['genre_ids'][1:]
            modified_data.append(movie_copy)

        return (self.movie_data, modified_data)

    def get_structured_data(self):
        MovieInfo = namedtuple('MovieInfo', ['title', 'popularity', 'score', 'last_day_in_cinema'])

        structured_data = []
        for movie in self.movie_data:
            # Parse release date
            release_date = movie.get('release_date')
            last_day = None
            if release_date:
                try:
                    release_dt = datetime.strptime(release_date, '%Y-%m-%d')
                    last_day = release_dt + timedelta(days=2 * 30 + 2 * 7)
                except ValueError:
                    pass

            # Create the structured data
            structured_data.append(MovieInfo(
                title=movie['title'],
                popularity=round(movie['popularity'], 1),
                score=int(movie['vote_average']),
                last_day_in_cinema=last_day.strftime('%Y-%m-%d') if last_day else None
            ))

        # Sort by score (descending) and popularity (descending)
        structured_data.sort(key=lambda x: (-x.score, -x.popularity))

        return structured_data

    def write_to_csv(self, file_path):
        structured_data = self.get_structured_data()

        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Title', 'Popularity', 'Score', 'Last_day_in_cinema'])

            for movie in structured_data:
                writer.writerow([
                    movie.title,
                    movie.popularity,
                    movie.score,
                    movie.last_day_in_cinema or 'N/A'
                ])