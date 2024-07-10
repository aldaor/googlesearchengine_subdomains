import os
import sys
import requests
import re
import random
from datetime import datetime, timedelta

def read_keys_counter_from_file(file_path):
    keys_counter = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            keys_counter = file.read().splitlines()
    return keys_counter

def write_keys_counter_to_file(file_path, keys_counter):
    with open(file_path, 'w') as file:
        file.write('\n'.join(keys_counter))

def update_key_counter(gse_keys_counter, gse_key, value, timestamp):
    existing_entry = next((entry for entry in gse_keys_counter if entry.startswith(gse_key)), None)
    if existing_entry:
        gse_keys_counter.remove(existing_entry)
    gse_keys_counter.append(f"{gse_key}|{value}|{timestamp}")

def reset_daily_counters(gse_keys_counter):
    for i in range(len(gse_keys_counter)):
        parts = gse_keys_counter[i].split('|')
        if len(parts) == 3 and parts[1] != "Banned":
            last_usage_time = datetime.fromisoformat(parts[2])
            if (datetime.now() - last_usage_time) >= timedelta(hours=24):
                gse_keys_counter[i] = f"{parts[0]}|0|{datetime.now().isoformat()}"

def parse_total_results(json_string):
    match = re.search(r'(?<="totalResults": ")[^"]*(?=")', json_string)
    return match.group(0) if match else None

def parse_and_store_results(json_string, query, gse_requests_path, gse_subdomains_path):
    items = re.findall(r'\{(.*?)\}', json_string, re.DOTALL)
    with open(gse_requests_path, 'a') as requests_file, open(gse_subdomains_path, 'a') as subdomains_file:
        for item in items:
            title = re.search(r'"title":\s*"([^"]+)"', item)
            link = re.search(r'"link":\s*"([^"]+)"', item)
            display_link = re.search(r'"displayLink":\s*"([^"]+)"', item)
            
            if title and link and display_link:
                request_entry = f"{query}|{display_link.group(1)}|{link.group(1)}|{title.group(1)}"
                subdomain_entry = display_link.group(1)
                requests_file.write(f"{request_entry}\n")
                subdomains_file.write(f"{subdomain_entry}\n")

def parse_error_code(json_string):
    match = re.search(r'"code":\s*(\d+)', json_string)
    return int(match.group(1)) if match else None

def build_url(query, key, cx, start, api_random):
    return f"https://customsearch.googleapis.com/customsearch/v1?num=10&q={query}&key={key}&cx={cx}&start={start}&callback=google.search.cse.api{api_random}&fileType=&exactTerms="

def main(base_path, gse_domain):
    # Read input files
    get_gse_keys = open(os.path.join(base_path, "gse_keys.txt")).read().splitlines()
    gse_search_modificators = open(os.path.join(base_path, "gse_search_modificators.txt")).read().splitlines()
    gse_keys_counter = read_keys_counter_from_file(os.path.join(base_path, "gse_keys_counter.txt"))

    domain_path = os.path.join(base_path, gse_domain)
    os.makedirs(domain_path, exist_ok=True)

    gse_requests_path = os.path.join(domain_path, "gse_requests.txt")
    gse_subdomains_path = os.path.join(domain_path, "gse_subdomains.txt")

    # Create empty files if they do not exist
    if not os.path.exists(gse_requests_path):
        open(gse_requests_path, 'w').close()
    if not os.path.exists(gse_subdomains_path):
        open(gse_subdomains_path, 'w').close()

    random_generator = random.Random()

    # Reset counters if needed
    reset_daily_counters(gse_keys_counter)

    if not gse_search_modificators:
        print("No search modifiers available. Stopping execution.")
        return

    gse_cx = ""
    gse_key = ""
    gse_key_counter = 0

    # Find a valid key
    for get_key in get_gse_keys:
        key_parts = get_key.split('|')
        if len(key_parts) == 2:
            gse_cx = key_parts[0]
            gse_key = key_parts[1]

            # Check the gse_keys_counter for this key's usage count
            counter_entry = next((entry for entry in gse_keys_counter if entry.startswith(gse_key)), None)
            if counter_entry:
                entry_parts = counter_entry.split('|')
                counter_value = entry_parts[1]
                last_usage_timestamp = entry_parts[2] if len(entry_parts) > 2 else datetime.min.isoformat()

                if counter_value == "Banned":
                    continue

                gse_key_counter = int(counter_value)

                # Check if 24 hours have passed since the last usage
                last_usage_time = datetime.fromisoformat(last_usage_timestamp)
                if (datetime.now() - last_usage_time) >= timedelta(hours=24):
                    gse_key_counter = 0

                if gse_key_counter < 100:
                    break
            else:
                gse_keys_counter.append(f"{gse_key}|0|{datetime.min.isoformat()}")
                break
        else:
            raise Exception("Invalid key format")

    if gse_key_counter >= 100:
        print("All keys have been used 100 times. Stopping execution.")
        return

    for gse_modificator in gse_search_modificators:
        gse_start_counter = 1  # Reset start counter for each modificator
        gse_query = f"site:{gse_domain}%20{gse_modificator}"
        cse_api_random = random_generator.randint(999, 6001)
        url = build_url(gse_query, gse_key, gse_cx, gse_start_counter, cse_api_random)

        try:
            print(f"Sending request to URL: {url}")
            response = requests.get(url)
            get_request1 = response.text
            # print(f"Response received: {get_request1[:200]}")  # Commented out this line

            # Parse the error code from the response
            error_code = parse_error_code(get_request1)
            if error_code == 429:
                # Quota exceeded
                update_key_counter(gse_keys_counter, gse_key, "100", datetime.now().isoformat())
                write_keys_counter_to_file(os.path.join(base_path, "gse_keys_counter.txt"), gse_keys_counter)
                continue
            elif error_code == 403:
                # Key banned
                update_key_counter(gse_keys_counter, gse_key, "Banned", datetime.now().isoformat())
                write_keys_counter_to_file(os.path.join(base_path, "gse_keys_counter.txt"), gse_keys_counter)
                continue

            response.raise_for_status()
            gse_total_results = parse_total_results(get_request1)

            if gse_total_results and int(gse_total_results) >= 100:
                while gse_start_counter < 91:
                    gse_start_counter += 10
                    url = build_url(gse_query, gse_key, gse_cx, gse_start_counter, random_generator.randint(999, 6001))
                    print(f"gse_total_results >= 100: {url}")
                    response = requests.get(url)
                    response.raise_for_status()
                    get_request1 = response.text
                    gse_key_counter += 1
                    parse_and_store_results(get_request1, gse_query, gse_requests_path, gse_subdomains_path)

            else:
                counter0 = 1
                gse_results_counter = (int(gse_total_results) + 9) // 10 if gse_total_results else 0

                while counter0 <= gse_results_counter:
                    counter0 += 1
                    gse_start_counter += 10
                    cse_api_random = random_generator.randint(999, 6001)
                    url = build_url(gse_query, gse_key, gse_cx, gse_start_counter, cse_api_random)
                    print(f"gse_total_results < 100: {url}")
                    response = requests.get(url)
                    response.raise_for_status()
                    get_request3 = response.text
                    gse_key_counter += 1
                    parse_and_store_results(get_request3, gse_query, gse_requests_path, gse_subdomains_path)

            # Update the counter in gse_keys_counter
            update_key_counter(gse_keys_counter, gse_key, str(gse_key_counter), datetime.now().isoformat())
            write_keys_counter_to_file(os.path.join(base_path, "gse_keys_counter.txt"), gse_keys_counter)

        except requests.RequestException as e:
            print(f"Request error: {e}")

    # Remove duplicates from gse_subdomains and save to file
    if os.path.exists(gse_subdomains_path):
        with open(gse_subdomains_path, 'r') as file:
            lines = file.readlines()
        unique_lines = set(lines)
        with open(gse_subdomains_path, 'w') as file:
            file.write(''.join(unique_lines))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: script.py <basePath> <gseDomain>")
        sys.exit(1)

    base_path = sys.argv[1]
    gse_domain = sys.argv[2]

    main(base_path, gse_domain)
