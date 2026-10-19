import hangtu as ht

columns = ht.columns("atterberg")
print(columns[["name", "quantity", "us_unit", "si_unit"]])
ht.template("atterberg").to_csv("my_atterberg.csv", index=False)
