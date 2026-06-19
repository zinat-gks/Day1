import pandas as pd

df = pd.read_csv("data/yessenov_pages.csv")

print(df[["title", "url", "text_length"]])
print("\nTotal pages:", len(df))

print("\nExample text:")
print(df.iloc[0]["text"][:1500])