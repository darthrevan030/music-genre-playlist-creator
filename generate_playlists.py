#!/usr/bin/env python3
"""
M3U Playlist Generator
Reads an Mp3tag CSV export and generates genre-based M3U playlist files.

Usage:
    python generate_playlists.py <input.csv> <output_folder>

Example:
    python generate_playlists.py music.csv ./playlists

The CSV must be exported from Mp3tag with at minimum these columns:
    Title;Artist;Album;Track;Year;Length;Size;Last Modified;Path;Filename;Genre;

Mp3tag export template:
    $filename(csv,utf-16)Title;Artist;Album;Track;Year;Length;Size;Last Modified;Path;Filename;Genre;
    $loop(%_filename_ext%)%title%;%artist%;%album%;%track%;%year%;%_length_seconds%;%_file_size%;%_file_mod_date%;%_folderpath%;%_filename_ext%;%genre%;
    $loopend()build on %_date% with %_app% - the universal Tag editor - http://www.mp3tag.de/en/
"""

import os
import sys

# ============================================================
# CONFIGURATION — edit these to customise your playlists
# ============================================================

# Artists to always put in Pop & Country regardless of genre tags
# (Singapore local artists)
SINGAPORE_ARTISTS = {
    "gareth fernandez", "rave republic", "charlie lim", "jasmine sokko",
    "nathan hartono", "daren yuen", "causeway youth", "taiyo amari",
    "shahrizal", "rangga jones", "linying", "fariz jabba", "sobs",
    "forests", "tabitha nauser"
}

# Artists to put in MULTIPLE playlists
# Format: "artist name lowercase": ["Playlist 1", "Playlist 2"]
MULTI_PLAYLIST_ARTISTS = {
    "when chai met toast": ["Pop & Country", "Bollywood & Desi"],
}

# Playlist definitions — ORDER MATTERS (most specific first)
# A track goes into the FIRST playlist whose keywords match any of its genre tags
PLAYLISTS = {
    "Pop Punk & Emo": [
        "pop punk", "emo", "post-hardcore", "skate punk"
    ],
    "Bollywood & Desi": [
        "bollywood", "desi", "hindi pop", "desi pop", "punjabi pop",
        "hindi indie", "indian indie", "sufi", "filmi", "india", "indian",
        "hindi", "indie-india", "bhangra", "punjabi", "pakistani", "pakistan"
    ],
    "Hip Hop, Rap & R&B": [
        "rap", "hip hop", "hip-hop", "desi hip hop", "trap", "urban contemporary",
        "rnb", "r&b", "rhythm and blues", "r b", "grime", "soul", "motown",
        "classic soul", "quiet storm", "funk"
    ],
    "EDM & Electronic": [
        "edm", "house", "tropical house", "big room", "progressive house",
        "future bass", "electronica", "electro", "electropop", "electronic",
        "trance", "dance", "drum and bass", "dnb", "liquid funk", "breakbeat",
        "disco", "hi-nrg", "coldwave", "minimal synth", "trip-hop", "downtempo"
    ],
    "Rock & Metal": [
        "rock", "alternative rock", "hard rock", "post-grunge", "soft rock",
        "indie rock", "alt-rock", "alternative", "powerpop", "power pop",
        "new wave", "punk", "metal", "alternative metal", "nu metal", "rap metal",
        "heavy metal", "metalcore", "hardcore", "thrashcore", "fastcore"
    ],
    "Folk, Indie & Chill": [
        "folk", "indie folk", "folk rock", "folk pop", "singer-songwriter",
        "ballad", "indie", "fingerstyle", "acoustic", "chill", "ambient", "lo-fi"
    ],
    "Soundtrack & Score": [
        "score", "soundtrack", "orchestral", "musical", "broadway"
    ],
    "Pop & Country": [
        "pop", "soft pop", "indie pop", "teen pop", "power pop", "boy band",
        "adult contemporary", "reggaeton", "latin", "country"
    ],
}

# ============================================================


def parse_csv(filepath):
    with open(filepath, encoding='utf-16') as f:
        content = f.read()

    lines = content.replace('\r\n', '\n').split('\n')
    tracks = []
    header = None

    for line in lines:
        line = line.strip()
        if not line or 'build on' in line or 'mp3tag.de' in line:
            continue
        parts = line.split(';')
        if parts[0] == 'Title':
            header = parts
            continue
        if header and len(parts) >= 10:
            tracks.append({
                'title': parts[0],
                'artist': parts[1],
                'album': parts[2],
                'filename': parts[9],
                'genre': parts[10].strip() if len(parts) > 10 else '',
            })

    return tracks


def classify_tracks(tracks):
    playlist_tracks = {name: [] for name in PLAYLISTS}
    unclassified = []

    for t in tracks:
        artist_lower = t['artist'].lower()
        all_genres = [g.strip().lower() for g in t['genre'].split(',') if g.strip()]
        entry = (t['title'], t['artist'], t['album'], t['filename'])

        # Multi-playlist artists
        if artist_lower in MULTI_PLAYLIST_ARTISTS:
            for playlist_name in MULTI_PLAYLIST_ARTISTS[artist_lower]:
                if playlist_name in playlist_tracks:
                    playlist_tracks[playlist_name].append(entry)
            continue

        # Singapore artists → Pop & Country
        if artist_lower in SINGAPORE_ARTISTS:
            playlist_tracks["Pop & Country"].append(entry)
            continue

        # Match by genre tags
        matched = None
        for playlist_name, keywords in PLAYLISTS.items():
            for genre in all_genres:
                if any(k in genre for k in keywords):
                    matched = playlist_name
                    break
            if matched:
                break

        if matched:
            playlist_tracks[matched].append(entry)
        else:
            unclassified.append(entry)

    return playlist_tracks, unclassified


def write_m3u(filepath, tracks):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for title, artist, album, filename in tracks:
            f.write(f"#EXTINF:-1,{artist} - {title}\n")
            f.write(f"{filename}\n")


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_playlists.py <input.csv> <output_folder>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_folder = sys.argv[2]

    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found")
        sys.exit(1)

    os.makedirs(output_folder, exist_ok=True)

    print(f"Reading {input_csv}...")
    tracks = parse_csv(input_csv)
    print(f"Found {len(tracks)} tracks")

    print("Classifying tracks...")
    playlist_tracks, unclassified = classify_tracks(tracks)

    print("\nPlaylist counts:")
    for name, tlist in playlist_tracks.items():
        if tlist:
            print(f"  {name}: {len(tlist)}")
            write_m3u(os.path.join(output_folder, f"{name}.m3u"), tlist)

    if unclassified:
        print(f"  Unclassified: {len(unclassified)}")
        write_m3u(os.path.join(output_folder, "Unclassified.m3u"), unclassified)

    print(f"\nPlaylists written to: {output_folder}")
    print("Done!")


if __name__ == "__main__":
    main()