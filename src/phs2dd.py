import requests
import os
import argparse
from bs4 import BeautifulSoup
import csv
from lxml import etree

parser = argparse.ArgumentParser(description="Make a GET request to a specified URL.")
parser.add_argument("-phs", "--phs_id", type=str, required=True, help="PHS id to scrape data dict from dbgap.")
args = parser.parse_args()

phs = args.phs_id

def get_lastest_version(study_url):
    try:
        response = requests.get(study_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        versions = [link.get('href').strip('/') for link in links if link.get('href').startswith(phs)]
        latest_version = max(versions, key=lambda x: int(x.split('.')[1][1:]))
        
        return latest_version
    
    except requests.exceptions.RequestException as e:
        # Handle possible errors, like network issues
        print(f"An error occurred: {e}")

def get_data_dict_str(pheno_var_sums_url):
    try:
        response = requests.get(pheno_var_sums_url)
        
        # Parse the response text to find the data dict
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        data_dicts = [link.get('href') for link in links if link.get('href').endswith('data_dict.xml')]
        return data_dicts

    except requests.exceptions.RequestException as e:
        # Handle possible errors, like network issues
        print(f"An error occurred: {e}")

def convert_xml_urls_to_csv(xml_urls):
    try:
        """
        For each URL in xml_urls (dbGaP 'data_dict.xml' files), downloads the file,
        parses it to extract <variable> data, and writes a CSV to disk.
        """
        for url in xml_urls:
            # 1) Download the XML
            response = requests.get(url)
            response.raise_for_status()  # Raise error if request failed

            # 2) Parse the XML with lxml
            #    etree.fromstring() expects bytes/string, so we pass response.content
            root = etree.fromstring(response.content)

            # 3) Build an output file name (replace .xml with .csv)
            #    Example: "phs001585.v4.pht008827.v4.FALS_Subject.data_dict.xml"
            #    becomes "phs001585.v4.pht008827.v4.FALS_Subject.data_dict.csv"
            base_name = os.path.basename(url)
            csv_name = base_name.replace(".xml", ".csv")

            # 4) Find <variable> elements
            variables = root.findall(".//variable")

            # 5) Write CSV
            with open(csv_name, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header row
                writer.writerow([
                    "id", 
                    "name", 
                    "description", 
                    "type", 
                    "unit", 
                    "logical_min", 
                    "logical_max", 
                    "coded_values", 
                    "comment"
                ])

                for var in variables:
                    var_id = var.get("id", "")
                    name = var.findtext("name", default="")
                    description = var.findtext("description", default="")
                    var_type = var.findtext("type", default="")
                    unit = var.findtext("unit", default="")
                    logical_min = var.findtext("logical_min", default="")
                    logical_max = var.findtext("logical_max", default="")
                    
                    # Collect coded values from any <value> children
                    coded_value_list = []
                    for val in var.findall("value"):
                        code = val.get("code", "")
                        val_text = val.text or ""
                        if code:
                            coded_value_list.append(f"{code}={val_text}")
                        else:
                            coded_value_list.append(val_text)
                    coded_values = "; ".join(coded_value_list)

                    comment = var.findtext("comment", default="")

                    writer.writerow([
                        var_id, 
                        name, 
                        description, 
                        var_type, 
                        unit, 
                        logical_min, 
                        logical_max, 
                        coded_values, 
                        comment
                    ])

            print(f"Saved CSV: {csv_name}")
    
    except requests.exceptions.RequestException as e:
        # Handle possible errors, like network issues
        print(f"An error occurred: {e}")

def main():
    study_url = f"https://ftp.ncbi.nlm.nih.gov/dbgap/studies/{phs}/"
    pheno_var_sums_url = f"{study_url}{get_lastest_version(study_url)}/pheno_variable_summaries/"
    data_dict_urls = []
    for data_dict_url in get_data_dict_str(pheno_var_sums_url):
        data_dict_urls.append(f"{pheno_var_sums_url}{data_dict_url}")
    convert_xml_urls_to_csv(data_dict_urls)
        
if __name__ == "__main__":
    main()    
    #todo: what to do if latest version data_dict is not available?
    #maybe get the previous latest version?

  
    # get_data_dict_data(data_dict_url)

    # To run this script, you would use the command line and provide the PHS id as an argument.
    # For example, if the PHS id is "phs000001", you would run:
    # python /Users/higbyfme/dev/ftd/phs2dd/phs2dd.py -phs phs000001
    #pip install lxml
    #pip install BeautifulSoup4
    #pip install requests
    #pip install argparse
    #pip install csv
