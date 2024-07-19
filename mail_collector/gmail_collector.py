from dataclasses import dataclass
from typing import List
from datetime import datetime
import os
import json
import time
from pathlib import Path
from tqdm import tqdm

from mail_collector.gmail_postman import GmailPostman_Attr, GmailPostman


@dataclass
class SearchQuery:
    query: str = None
    start_date: datetime = datetime(2000, 1, 1)
    end_date: datetime = datetime.now()
    max_results: int = int(1e7)
    

@dataclass
class GmailCollector_Attr:
    
    run_name: str
    
    search_queries: List[SearchQuery]
    
    gmail_postman_attr: GmailPostman_Attr = GmailPostman_Attr()
    
    # scheduling parameters
    sleep_time: int = 0.01    # sleep time in seconds
    max_retries: int = 3    # maximum number of retries
    retry_sleep_time: int = 5    # sleep time in seconds between retries
    
    # logging parameters
    log_folder: str = str(Path("./mount/logs"))
    

class GmailCollector:
    def __init__(self, attr: GmailCollector_Attr):
        self.attr = attr 
        
        self.gmail_postman = GmailPostman(attr.gmail_postman_attr)
        
        # Get the list of emails to be collected
        self.search_query_results = self._search_queries()
        
        # save the collection plan
        self.save_folder = self._save_collection_plan()
        
        # log details
        self.completed_logfile = os.path.join(self.save_folder, "completed_log.json")
        self.error_logfile = os.path.join(self.save_folder, "error_log.json")
        
    
    def _search_queries(self):
        search_query_results = []
        for search_query in self.attr.search_queries:
            if search_query.query is not None:
                total_query = search_query.query
            else:
                total_query = ""
            if search_query.start_date is not None:
                start_date = search_query.start_date.strftime("%Y/%m/%d")
                total_query += f" after:{start_date}"
            if search_query.end_date is not None:
                end_date = search_query.end_date.strftime("%Y/%m/%d")
                total_query += f" before:{end_date}"
            search_query_result = self.gmail_postman.search_messages(total_query)
            search_query_results.append(search_query_result[:search_query.max_results])
            
        return search_query_results
    
    
    def _save_collection_plan(self):
        folder_name = "gmail_collect" + datetime.now().strftime("%Y%m%d_%H%M")
        os.makedirs(os.path.join(self.attr.log_folder, folder_name))
        
        run_details = self.attr.__dict__
        run_details['search_queries'] = [{ k:v.strftime("%Y/%m/%d_%H:%M") if 'date' in k else v for k,v in sq.__dict__.items() } for sq in run_details['search_queries']] 
        run_details['gmail_postman_attr'] = { k:v for k,v in run_details['gmail_postman_attr'].__dict__.items()}
        run_details["number_of_search_results"] = [len(search_query_result) for search_query_result in self.search_query_results]
        
        with open(os.path.join(self.attr.log_folder, folder_name, f"collection_plan.json"), "w") as f:
            json.dump(run_details, f)
            
        with open(os.path.join(self.attr.log_folder, folder_name, f"search_query_results.json"), "w") as f:
            dump_results = {f"search_query_{i}": [m['id'] for m in search_query_result] for i, search_query_result in enumerate(self.search_query_results)}
            json.dump(dump_results, f)
            
        return os.path.join(self.attr.log_folder, folder_name)
    
    
    def start_mail_collection(self):
        for i, search_query_result in enumerate(self.search_query_results):
            print(f" ||>> Collecting for search query {i}...")
            for search_result in tqdm(search_query_result):
                retries = 0
                while retries < self.attr.max_retries:
                    try:
                        _ = self.gmail_postman.read_message(search_result)
                        with open(self.completed_logfile, "a") as f:
                            f.write(f"{search_result['id']}\n")
                        break
                    except Exception as e:
                        with open(self.error_logfile, "a") as f:
                            f.write(f"{search_result['id']}|{e}\n")
                        retries += 1
                        time.sleep(self.attr.retry_sleep_time)
                        self.gmail_postman.service = self.gmail_postman._gmail_authenticate()
                        
                time.sleep(self.attr.sleep_time)