
import pandas as pd
data = {
    "Name": ["Asha", "Rahul", "Meena", "Arun", "Sara", "Vikram"],
    "Department": ["IT", "HR", "IT", "Finance", "HR", "IT"],
    "Age": [23, 28, 25, 32, 26, 30],
    "Salary": [45000, 52000, 60000, 75000, 48000, 68000],
    "City": ["Chennai", "Bangalore", "Chennai", "Mumbai", "Bangalore", "Chennai"]
}
df = pd.DataFrame(data)
(df)