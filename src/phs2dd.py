import requests
import os
import argparse
from bs4 import BeautifulSoup
import csv
import logging
from lxml import etree

# Configure logging
logging.basicConfig(
    filename='phs2dd.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_lastest_version(study_url, phs_id):
    try:
        response = requests.get(study_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        versions = [link.get('href').strip('/') for link in links if link.get('href').startswith(phs_id)]
        
        if not versions:
            logging.error(f"No data dictionaries found for PHS ID: {phs_id} at {study_url}")
            return None
        
        latest_version = max(versions, key=lambda x: int(x.split('.')[1][1:]))
        return latest_version
    
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

def get_data_dict_str(pheno_var_sums_url):
    try:
        response = requests.get(pheno_var_sums_url)
        
        # Parse the response text to find the data dict
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        data_dicts = [link.get('href') for link in links if link.get('href').endswith('data_dict.xml')]
        if data_dicts == []:
            logging.error(f"{pheno_var_sums_url}: No data_dict.xml found")
            

        return data_dicts

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

def convert_xml_urls_to_csv(xml_urls):
    try:
        """
        For each URL in xml_urls (dbGaP 'data_dict.xml' files), downloads the file,
        parses it to extract <variable> data, and writes a CSV to disk.
        """
        for url in xml_urls:
            response = requests.get(url)
            response.raise_for_status() 

            root = etree.fromstring(response.content)

            base_name = os.path.basename(url)
            csv_name = base_name.replace(".xml", ".csv")

            variables = root.findall(".//variable")


            with open(csv_name, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header row
                writer.writerow([
                    "variable_name", 
                    "description", 
                    "type", 
                    "min", 
                    "max", 
                    "units", 
                    "enumerations", 
                    "comment",
                    "dbgap_id"
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
                        name, 
                        description, 
                        var_type, 
                        logical_min, 
                        logical_max, 
                        unit, 
                        coded_values,
                        comment,
                        var_id 
                    ])

            print(f"Saved CSV: {csv_name}")
            logging.info(f"Saved CSV: {csv_name}")
    
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

def main(phs_ids):
    for phs_id in phs_ids:
        study_url = f"https://ftp.ncbi.nlm.nih.gov/dbgap/studies/{phs_id}/"
        latest_version = get_lastest_version(study_url, phs_id)
        
        if latest_version is None:
            continue
        
        pheno_var_sums_url = f"{study_url}{latest_version}/pheno_variable_summaries/"
        data_dict_urls = []
        for data_dict_url in get_data_dict_str(pheno_var_sums_url):
            data_dict_urls.append(f"{pheno_var_sums_url}{data_dict_url}")
        convert_xml_urls_to_csv(data_dict_urls)
        logging.info(f"Processed PHS ID: {phs_id}, Data Dict URLs: {data_dict_urls}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make a GET request to a specified URL.")
    parser.add_argument("-phs", "--phs_ids", type=str, nargs='+', required=True, help="PHS ids to scrape data dict from dbgap.")
    args = parser.parse_args()
    phs_ids = args.phs_ids
    main(phs_ids)
    #todo: what to do if latest version data_dict is not available?
    #yes get the previous latest version.
    #create a log if it cant find the latest version and then get the previous version. timestamp log to the second. also how many vars found
    #also log successes.

  
    # get_data_dict_data(data_dict_url)

    # To run this script, you would use the command line and provide the PHS id as an argument.
    # For example, if the PHS id is "phs000001", you would run:
    # python ./src/phs2dd.py -phs phs000001
    #pip install lxml
    #pip install BeautifulSoup4
    #pip install requests
    #pip install argparse
    #pip install csv
