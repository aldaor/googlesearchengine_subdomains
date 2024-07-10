# googlesearchengine_subdomains
This project is a Python script designed to scrape subdomains using Google Custom Search Engine (GSE). The script reads a list of API keys, search modifiers, and manages the usage of these keys to avoid exceeding usage limits. Results are stored in text files, and duplicates are removed at the end of each run.


- `scripts/gse_keys.txt`: Contains API keys and their associated CX values.
- `scripts/gse_search_modificators.txt`: Contains search modifiers.
- `scripts/gse_keys_counter.txt`: Tracks usage of API keys.
- `scripts/gseSubdomains.py`: Main script to run the scraper.

## Prerequisites

- Python 3.x
- `requests` library: Install via `pip install requests`

## Usage

1. Clone the repository:
    ```sh
    git clone https://github.com/your-username/gse-subdomain-scraper.git
    cd gse-subdomain-scraper
    ```

2. Navigate to the `scripts` directory:
    ```sh
    cd scripts
    ```

3. Ensure the `gse_keys.txt`, `gse_search_modificators.txt`, and `gse_keys_counter.txt` files are populated with the necessary data.

4. Run the script:
    ```sh
    python3 gseSubdomains.py /path/to/your/base/directory your-domain.com
    ```

5. Example:
    ```sh
    python3 gseSubdomains.py /home/dock/bugsmatic/bugsmatic/scripts redbull.com
    ```

## Notes

- The script will create and update `gse_requests.txt` and `gse_subdomains.txt` in the specified base directory.
- Duplicate subdomains will be removed at the end of each script run.

## License

This project is licensed under the MIT License.
