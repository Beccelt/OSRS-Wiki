#!/usr/bin/env python
# coding: utf-8

import requests
from bs4 import BeautifulSoup
from datetime import date
import numpy as np

# Define headers to bypass bot protection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Fetch the current 200m XP table from OSRS Wiki
wiki_url = 'https://oldschool.runescape.wiki/w/Module:200mxp/data'
response = requests.get(wiki_url, headers=HEADERS)
wiki_contents = BeautifulSoup(response.content, 'html.parser')

# Extract numerical data from spans with class "mi"
entries = [i.text for i in wiki_contents.find_all('span', class_='mi')]

# Ensure we have enough data
if len(entries) != 24 * 4:
    print("Error: Extracted data does not match expected 24x4 table size.")
    print(f"Entries found: {len(entries)}")
    exit(1)

table = np.reshape(entries, (24, 4))

# Print current data
print('Old data:')
print(table)
print("\nUpdating data... This may take a minute.\n")

# Hiscore base URL
hiscore_base = 'https://secure.runescape.com/'
acc_types = ['m=hiscore_oldschool/', 'm=hiscore_oldschool_ironman/',
             'm=hiscore_oldschool_ultimate/', 'm=hiscore_oldschool_hardcore_ironman/']
skills = [str(i+1) if i != 23 else '0' for i in range(24)]

# Scraping loop
for skill_index, skill_id in enumerate(skills):
    threshold = 4600000000 if skill_id == '0' else 200000000

    for acc_index, acc_type in enumerate(acc_types):
        last = True
        extra_pages = 0

        while last:
            try:
                # Construct Hiscores URL
                current_page = int(table[skill_index][acc_index]) // 25 + 1 + extra_pages
                url = f"{hiscore_base}{acc_type}overall?table={skill_id}&page={current_page}"
                response = requests.get(url, headers=HEADERS)
                
                # Parse the page
                page = BeautifulSoup(response.content, 'html.parser')
                hiscores = page.find_all('td')

                # Debugging output
                if extra_pages == 0:
                    print(f"Fetching: {url}")
                    print(f"Found {len(hiscores)} table elements")

                # Ensure we have enough data
                if len(hiscores) < 8:
                    print(f"Skipping {url} - unexpected structure.")
                    break

                start = int(table[skill_index][acc_index]) % 25 if extra_pages == 0 else 0

                # Extract XP values safely
                xp = []
                for k in range(start, min(24, len(hiscores)//4)):  # Avoid out-of-bounds errors
                    try:
                        xp_value = int(hiscores[4*k+7].text.strip().replace(',', ''))
                        xp.append(xp_value)
                    except (IndexError, ValueError):
                        print(f"Skipping index {4*k+7}, data unavailable.")
                
                # Check for completion
                indices = [i for i in xp if i < threshold]
                if indices:
                    diff = (24-len(indices)) - int(table[skill_index][acc_index]) % 25 + 25 * extra_pages
                    table[skill_index][acc_index] = str(int(table[skill_index][acc_index]) + diff)
                    print(f"Updated {url}: {table[skill_index][acc_index]} ( +{diff} )")
                    last = False
                else:
                    extra_pages += 1

            except Exception as e:
                print(f"Error on {url}: {e}")
                last = False

# Print new table
print('\nNew data:')
print(table)

# Format data for OSRS Wiki module
formatted_text = ("-- skill = all, im, uim, hcim\nreturn {{\n"
    + "\n".join([f"\t['{skill}'] = {{{', '.join(table[i])}}}," for i, skill in enumerate(
        ['attack', 'defence', 'strength', 'hitpoints', 'ranged', 'prayer', 'magic', 'cooking', 'woodcutting', 'fletching', 'fishing', 'firemaking', 'crafting', 'smithing', 'mining', 'herblore', 'agility', 'thieving', 'slayer', 'farming', 'runecraft', 'hunter', 'construction', 'overall'] )])
    + f"\n\t['update'] = '{date.today().strftime('%d %B %Y')}'\n}}")

# Display formatted data
print("\nFormatted text for Module:200mxp/data:")
print(formatted_text)