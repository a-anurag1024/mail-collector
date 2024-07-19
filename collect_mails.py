from datetime import datetime

from gmail_collector.gmail_collector import GmailCollector_Attr, SearchQuery, GmailCollector

query_1 = SearchQuery(query=None, 
                      start_date=datetime(2023, 1, 1), 
                      end_date=datetime(2024, 7, 31)
                      )

collector_attributes = GmailCollector_Attr(run_name="test_run",
                                           search_queries=[query_1],
                                           )

collector = GmailCollector(attr=collector_attributes)

# launch the collection 
collector.start_mail_collection()