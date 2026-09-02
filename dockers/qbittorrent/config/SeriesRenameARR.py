#!/usr/bin/env python3

import os
import shutil
import re
import argparse
import sys
import time

# Keep only the media and subtitle files. Everything else gets trashed.
KEEP_EXTENSIONS = {
    ".mkv", ".mp4", ".avi", ".m4v", ".ts", ".m2ts", ".webm", ".flv", ".wmv", 
    ".srt", ".ass", ".vtt", ".sub", ".idx"
}

# The STRICT Allow List for qBittorrent Categories. 
# The script will ONLY run if the torrent matches one of these exactly.
ALLOWED_CATEGORIES = {
    "tv", "sonarr", "series", "shows", "tv-sonarr",
    "movies", "movie", "radarr"
}

ALLOWED_CATEGORIES_MOVIES = {
    "movies", "movie", "radarr"
}

# --- Set to "copy" to seed torrents, or "move" to delete original files ---
OPERATION_MODE = "move"

# Regex to chop off the season/episode/year tags to find the raw Series Name
CUTOFF_PATTERN = re.compile(
    r"(\b(19|20)\d{2}\b)|"          # Stops at Year (e.g., 2014)
    r"(\b[sS]\d{2,}\b)|"            # Stops at S01
    r"(\b[sS]\d{2,}[eE]\d{2,}\b)|"  # Stops at S01E01
    r"(\bSeason\s*\d+\b)|"          # Stops at Season 1
    r"(\b\d{1,2}x\d{2,}\b)",        # Stops at 1x01
    re.IGNORECASE
)

def clean_series_name(raw: str, merge_years: bool) -> str:
    clean_name = raw.replace(".", " ").replace("_", " ")
    clean_name = re.sub(r"[\[\(].*?[\]\)]", "", clean_name)

    # Extract the year before chopping the string
    year_match = re.search(r"\b((19|20)\d{2})\b", clean_name)
    extracted_year = f" ({year_match.group(1)})" if year_match else ""

    match = CUTOFF_PATTERN.search(clean_name)
    if match:
        clean_name = clean_name[:match.start()]

    # Clean residual scene tags
    clean_name = re.sub(
        r"\b(hdtv|webrip|bluray|brrip|web[- ]?dl|x264|x265|1080p|720p|480p|complete|series)\b",
        "", clean_name, flags=re.IGNORECASE
    )
    
    final_name = " ".join(clean_name.split()).strip().title()
    final_name = final_name if final_name else raw.replace(".", " ").strip().title()

    # Append the year if the user chose to keep different years separate
    if not merge_years and extracted_year:
        return f"{final_name}{extracted_year}"
    
    return final_name

def extract_season(filename: str) -> str:
    # Looks for S01, 1x01, or Season 1
    s_match = re.search(r"[sS](\d+)", filename)
    if s_match:
        return f"Season {int(s_match.group(1)):02d}"

    x_match = re.search(r"(?<!\d)(\d{1,2})x\d{2,}(?!\d)", filename)
    if x_match:
        return f"Season {int(x_match.group(1)):02d}"

    season_match = re.search(r"Season\s*(\d+)", filename, re.IGNORECASE)
    if season_match:
        return f"Season {int(season_match.group(1)):02d}"

    return "Season 01"

def process_torrent_folder(folder_path: str, complete_dir: str, merge_years: bool):
    """Handles parsing and moving standard TV Show folders."""
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    folder_path = os.path.normpath(folder_path)
    raw_folder_name = os.path.basename(folder_path)
    
    series_name = clean_series_name(raw_folder_name, merge_years)
    season = extract_season(raw_folder_name)
    
    # Create the clean structure inside the user-defined Complete Directory
    target_dir = os.path.join(complete_dir, series_name, season)
    os.makedirs(target_dir, exist_ok=True)

    print(f"\nProcessing TV Show: '{raw_folder_name}'")
    print(f"Target Directory: '{target_dir}'")

    # Walk through the torrent folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            src_file = os.path.join(root, file)

            # Trash junk extensions and sample files (ONLY if moving)
            if ext not in KEEP_EXTENSIONS or "sample" in file.lower():
                if OPERATION_MODE == "move":
                    try:
                        os.remove(src_file)
                        print(f"  -> Deleted Junk: {file}")
                    except Exception:
                        pass
                else:
                    print(f"  -> Ignored Junk (Seeding Mode): {file}")
                continue

            # Move valid files absolutely UNTOUCHED
            dst_file = os.path.join(target_dir, file)
            
            # Prevent crashing if the file is already there
            counter = 1
            file_base, file_ext = os.path.splitext(dst_file)
            while os.path.exists(dst_file) and src_file != dst_file:
                dst_file = f"{file_base} ({counter}){file_ext}"
                counter += 1
            
            if src_file != dst_file:
                # --- NEW ROBUST OPERATION LOGIC FOR HEAVY DRIVE LOADS ---
                max_retries = 10
                for attempt in range(1, max_retries + 1):
                    try:
                        if OPERATION_MODE == "copy":
                            shutil.copy2(src_file, dst_file)
                            print(f"  -> Copied Untouched: {file}")
                        else:
                            shutil.move(src_file, dst_file)
                            print(f"  -> Moved Untouched: {file}")
                        break  # Break out of the retry loop if successful
                    except Exception as e:
                        if attempt < max_retries:
                            print(f"  -> Drive busy or file locked. Retrying {file} in 15s... (Attempt {attempt}/{max_retries})")
                            time.sleep(15)
                        else:
                            action_name = "copy" if OPERATION_MODE == "copy" else "move"
                            print(f"  -> ERROR: Failed to {action_name} {file} after {max_retries} attempts: {e}")
                # -----------------------------------------------------

    # Safely clean up leftover empty folders from the bottom up
    if OPERATION_MODE == "move":
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
        try:
            os.rmdir(folder_path)
            print("  -> Cleaned up original torrent folder.")
        except OSError:
            pass

    print("-" * 40)

def process_movie_folder(input_path: str, dest_dir: str):
    """Handles creating movie folders, stripping Greek parentheses, and transferring."""
    input_path = os.path.normpath(input_path)
    
    # 1. Determine if the input is a single file or a directory
    if os.path.isfile(input_path):
        filename = os.path.basename(input_path)
        raw_name, _ = os.path.splitext(filename)
        is_file = True
    elif os.path.isdir(input_path):
        raw_name = os.path.basename(input_path)
        is_file = False
    else:
        print(f"Error: '{input_path}' is not valid.")
        return

    # 2. Clean Greek characters for the final folder name
    clean_name = re.sub(r'\s*\([^)]*[\u0370-\u03FF\u1F00-\u1FFF]+[^)]*\)', '', raw_name).strip()
    new_folder_name = clean_name if clean_name else raw_name
    
    # 3. Create the final movie folder in the destination directory
    target_dir = os.path.join(dest_dir, new_folder_name)
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"\nProcessing Movie: '{raw_name}'")
    print(f"Target Directory: '{target_dir}'")
    
    # Helper to handle the physical file transfer (with retries)
    def transfer_file(src, dst, fname):
        counter = 1
        file_base, file_ext = os.path.splitext(dst)
        while os.path.exists(dst) and src != dst:
            dst = f"{file_base} ({counter}){file_ext}"
            counter += 1
            
        if src == dst: return

        max_retries = 10
        for attempt in range(1, max_retries + 1):
            try:
                if OPERATION_MODE == "copy":
                    shutil.copy2(src, dst)
                    print(f"  -> Copied: {fname}")
                else:
                    shutil.move(src, dst)
                    print(f"  -> Moved: {fname}")
                break
            except Exception as e:
                if attempt < max_retries:
                    print(f"  -> Drive busy. Retrying {fname} in 15s... (Attempt {attempt}/{max_retries})")
                    time.sleep(15)
                else:
                    print(f"  -> ERROR: Failed to transfer {fname}: {e}")

    # 4. Transfer Logic
    if is_file:
        # Handle single video file without a folder
        ext = os.path.splitext(input_path)[1].lower()
        if ext in KEEP_EXTENSIONS and "sample" not in filename.lower():
            dst_file = os.path.join(target_dir, filename)
            transfer_file(input_path, dst_file, filename)
        elif OPERATION_MODE == "move":
            os.remove(input_path)
    else:
        # Handle standard torrent folder
        for root, dirs, files in os.walk(input_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                src_file = os.path.join(root, file)

                if ext not in KEEP_EXTENSIONS or "sample" in file.lower():
                    if OPERATION_MODE == "move":
                        try:
                            os.remove(src_file)
                            print(f"  -> Deleted Junk: {file}")
                        except Exception:
                            pass
                    continue

                dst_file = os.path.join(target_dir, file)
                transfer_file(src_file, dst_file, file)

        # 5. Cleanup original directory if moving
        if OPERATION_MODE == "move":
            for root, dirs, files in os.walk(input_path, topdown=False):
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError: pass
            try:
                os.rmdir(input_path)
                print("  -> Cleaned up original movie folder.")
            except OSError: pass
            
    print("-" * 40)

def rename_movie_in_place(input_path: str):
    """Renames the movie folder right where it sits if no destination was provided."""
    input_path = os.path.normpath(input_path)
    
    # We can only rename folders, not single files
    if not os.path.isdir(input_path):
        print("Ignored: Movie is a single file, not a folder. Nothing to rename.")
        return

    parent_dir = os.path.dirname(input_path)
    raw_name = os.path.basename(input_path)
    
    # Clean Greek characters in parentheses
    clean_name = re.sub(r'\s*\([^)]*[\u0370-\u03FF\u1F00-\u1FFF]+[^)]*\)', '', raw_name).strip()
    new_folder_name = clean_name if clean_name else raw_name
    
    if new_folder_name != raw_name:
        new_path = os.path.join(parent_dir, new_folder_name)
        if not os.path.exists(new_path):
            try:
                os.rename(input_path, new_path)
                print(f"Success: Renamed original movie folder to '{new_folder_name}'")
            except Exception as e:
                print(f"Error renaming folder: {e}")
        else:
            print(f"Error: Target folder '{new_folder_name}' already exists. Aborting rename.")
    else:
        print("Ignored: Folder does not contain Greek parenthesis tags. No rename needed.")

def main():
    parser = argparse.ArgumentParser(description="Jellyfin Source-to-Destination Sorter")
    parser.add_argument("-i", "--input", required=True, help="The incomplete torrent folder to process")
    parser.add_argument("-s", "--series-dir", required=True, help="The destination FinishedSeries folder")
    parser.add_argument("-m", "--movies-dir", required=False, help="The destination FinishedMovies folder")
    parser.add_argument("--separate-years", required=True, choices=['true', 'false'], type=str.lower, help="Set to 'true' to keep reboots separate, 'false' to merge them")
    parser.add_argument("--in-place-rename", required=False, default="false", choices=['true', 'false'], type=str.lower, help="Set to 'true' to rename the original folder if no -m folder is provided")
    parser.add_argument("--category", required=False, default="", help="The qBittorrent category")
    
    args = parser.parse_args()

    # --- The Strict Allow-List Fail-Safe ---
    category_lower = args.category.strip().lower()
    
    # If the category is uncategorized (empty string) or anything NOT in our allowed list
    if category_lower not in ALLOWED_CATEGORIES:
        display_name = category_lower if category_lower else "Uncategorized"
        print(f"Ignored: Category '{display_name}' is not an approved category. Leaving folder untouched.")
        sys.exit(0)
    # ----------------------------------------

    input_path = os.path.normpath(args.input)
    complete_path = os.path.normpath(args.series_dir)
    
    if category_lower in ALLOWED_CATEGORIES_MOVIES:
        
        # Scenario 1: A destination movie folder WAS provided. Move the file normally.
        if args.movies_dir:
            movie_dest = os.path.normpath(args.movies_dir)
            process_movie_folder(input_path, movie_dest)
            
        # Scenario 2: No destination provided, but in-place rename is ENABLED
        elif args.in_place_rename == "true":
            print("Notice: No movies directory (-m) was set, but in-place rename is enabled. Renaming folder...")
            rename_movie_in_place(input_path)
            
        # Scenario 3: No destination provided, and in-place rename is DISABLED (or omitted)
        else:
            print("Ignored: No movies directory (-m) was set, and --in-place-rename is false. Leaving movie untouched.")
            sys.exit(0)
            
    else:
        # Route to the standard TV Show logic
        merge_years = False if args.separate_years == 'true' else True
        process_torrent_folder(input_path, complete_path, merge_years)

if __name__ == "__main__":
    main()