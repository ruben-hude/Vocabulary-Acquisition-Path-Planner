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
    my_books_to_download = [84, 1342, 11, 1513, 2701, 1661, 98, 1232, 345, 64317]
    
    print("Starting download process...")
    download_books_by_ids(my_books_to_download)
    print("\nAll downloads completed!")