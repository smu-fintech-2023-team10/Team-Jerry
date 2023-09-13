from transformers import pipeline
import pandas as pd
import re

sentiment_pipeline = pipeline("sentiment-analysis") #create sentiment analysis model
scan_to_pay_df = pd.read_csv('../csv/scan_to_pay.csv') #read scan to pay df
unrecognised_msgs = scan_to_pay_df["msgs_to_customer_support"].tolist() #get msgs_to_customer_support column

msgs = []
pattern = r'["\'\[\]]'

for lst in unrecognised_msgs:
    lst = lst.split(", ") # transform string representation of array to array ie "[['msg1', 'msg2'], ['msg3', 'msg4']]" to [['msg1', 'msg2'], ['msg3', 'msg4']]
    for msg in lst:
            msg = re.sub(pattern, '', msg) # remove ' " [ ] from msg
            msg = msg.strip() # remove spaces from the start and end of msg
            if msg != "": # msgs_to_customer_support column is []
                msgs.append(msg)

sentiments = sentiment_pipeline(msgs) # apply sentiment analysis

# turn msgs and sentiment into a csv
msgs_sentiments = {"msgs": msgs, "sentiments": sentiments}
msgs_sentiments_df = pd.DataFrame(msgs_sentiments)
msgs_sentiments_df.to_csv("../csv/scan_to_pay_sentiments.csv", index=False)


