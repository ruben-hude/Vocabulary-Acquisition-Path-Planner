import os
import gutenbergpy.textget

# Configuration: Folder where texts will be saved
DOWNLOAD_FOLDER = "data/raw/gutenberg_books"

def download_books_by_ids(id_list):
    """
    Takes a list of Gutenberg IDs, downloads each book,
    cleans the headers/footers, and saves them into the download folder.
    """
    # Create the folder if it does not exist
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)
        print(f"Created directory: {DOWNLOAD_FOLDER}")
        
    for book_id in id_list:
        print(f"\nProcessing book ID: {book_id}...")
        filename = os.path.join(DOWNLOAD_FOLDER, f"book_{book_id}.txt")
        
        try:
            # 1. Fetch raw compressed data from Project Gutenberg
            raw_book = gutenbergpy.textget.get_text_by_id(book_id)
            
            # 2. Strip standard Gutenberg licensing text (headers and footers)
            clean_book = gutenbergpy.textget.strip_headers(raw_book)
            
            # 3. Decode bytes to standard UTF-8 string
            book_text = clean_book.decode('utf-8')
            
            # 4. Save to local folder
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(book_text)
                
            print(f"-> Successfully saved to: {filename}")
            
        except Exception as e:
            print(f"-> Error downloading book {book_id}: {e}")

if __name__ == "__main__":
    # Define the list of IDs you want to download here
    # Example: 84 (Frankenstein), 135 (Les Misérables), 11 (Alice in Wonderland)
    my_books_to_download = [
    1342, 84, 2701, 11, 1661, 345, 98, 1400, 1260, 174, 
    2554, 74, 76, 5200, 514, 1184, 205, 1727, 2600, 253, 
    768, 55, 120, 46, 844, 2814, 1497, 2680, 158, 35, 
    36, 2542, 60, 161, 105, 121, 141, 829, 521, 215, 
    910, 41, 1952, 219, 43, 600, 2805, 2199, 996, 61, 
    408, 23, 203, 3825, 160, 110, 107, 143, 2852, 244, 
    2097, 45, 113, 16, 12, 1080, 1322, 14, 180, 209, 
    164, 1888, 103, 863, 1153, 1232, 19942, 4300, 108, 976, 
    1255, 149, 139, 153, 195, 216, 308, 320, 405, 421, 
    500, 522, 613, 711, 801, 901, 1001, 1112, 1221, 1333
]
    
    print("Starting download process...")
    download_books_by_ids(my_books_to_download)
    print("\nAll downloads completed!")