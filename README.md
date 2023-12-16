# Music Events Recommender

## Overview

This project utilizes the Spotify and Ticketmaster APIs to recommend music events based on a user's favorite artist. It generates a list of top 5 artists with similar musical styles and provides information about their upcoming events.

### GitHub Repository

[Link to GitHub Repo](https://github.com/renashen314/recommend_music_events)

## Getting Started

### API Keys

1.  **Spotify API Key:**

    - Follow the instructions in [this video](https://chat.openai.com/c/SPOTIFY_API_VIDEO_LINK) to obtain a Spotify API key.
    - Use the obtained key for authorization to access the Spotify API.

2.  **Ticketmaster API Key:**

    - Obtain a Ticketmaster API key from [Ticketmaster Developer Portal](https://developer.ticketmaster.com/products-and-docs/apis/getting-started/).
    - Replace the placeholder `TM_KEY` in `main.py` and `app.py` with your Ticketmaster API key.

### Interacting with the Program

The interaction with the program is done through a web page. Follow these steps:

1.  Enter your favorite artist's name on the index page.
2.  Click the "Get Recommendation" button.
3.  The program generates the top 5 similar artists.
4.  Optionally, click on the "Get Events" button to see a list of events by these artists.
5.  Each event is a hyperlink leading to the event details page.

### Required Python Packages

- `python-dotenv`
- `requests`
- `flask`

### Running the Program

In the command line, run the following command:

    $ flask --app app run

## Data Sources

### Spotify API

- [Spotify API Documentation](https://developer.spotify.com/documentation/web-api)
- **Response Format:** JSON
- **Authorization:** OAuth 2.0
- **Endpoints Used:**
  - `/search`: Search for an artist using the artist's name.
  - `/artists/{id}/related-artists`: Get related artists for a given artist ID.

### Ticketmaster Discovery API

- [Ticketmaster API Documentation](https://developer.ticketmaster.com/products-and-docs/apis/getting-started/)
- **Response Format:** JSON
- **Authorization:** OAuth 2.0
- **Endpoints Used:**
  - `/discovery/v2/attractions`:Attraction Search: Find attractions (artists, sports, packages, plays, etc.).
  - `/discovery/v2/events`:Event Search: Find events by location, date, availability, etc.

## Data Structure

The program uses a graph data structure to calculate the most related top 5 artists based on their genres. Nodes represent artists, and edges connect artists with the same genre. Similarity scores are calculated based on the overlap of genres.

## Interaction and Presentation Options

- The user interacts with the application through a web page.
- Enter a favorite artist, click "Get Recommendation" to see the top 5 similar artists.
- Optionally, click "Get Events" to see a list of events by each artist.
- Events are presented as hyperlinks leading to the event details page.

## Demo

Watch the demo [here](https://drive.google.com/file/d/1HkG9hyJAoCB_JFZ1tWIGBLs8GxgLW_ig/view?usp=sharing) (includes audio).

Feel free to explore the project, provide feedback, and contribute to its development!
