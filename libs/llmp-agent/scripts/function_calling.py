from convert import convert_to_openai_function, convert_to_openai_tool
from pydantic.v1 import BaseModel, Field
from datetime import datetime
from pprint import pp


class OutputSchemaExpense(BaseModel):
    description: str = Field(description="The description of the expense or what the amount was spend for.")
    net_expense: float
    gross_expense: float
    tax_rate: float
    date: datetime


pp(convert_to_openai_function(OutputSchemaExpense))
print("\n-----------------\n")
pp(convert_to_openai_tool(OutputSchemaExpense))
