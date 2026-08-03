import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine
from smolagents import (ToolCallingAgent, OpenAIServerModel, tool,)
print(os.getcwd())

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]
CATALOG_ITEM_NAMES = ", ".join(
    item["item_name"] for item in paper_supplies
)
# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    Insert one transaction and return its database ID.
    """
    if transaction_type not in {"stock_orders", "sales"}:
        raise ValueError(
            "Transaction type must be 'stock_orders' or 'sales'"
        )

    date_str = date.isoformat() if isinstance(date, datetime) else date

    insert_query = text("""
        INSERT INTO transactions (
            item_name,
            transaction_type,
            units,
            price,
            transaction_date
        )
        VALUES (
            :item_name,
            :transaction_type,
            :units,
            :price,
            :transaction_date
        )
    """)

    with db_engine.begin() as connection:
        result = connection.execute(
            insert_query,
            {
                "item_name": item_name,
                "transaction_type": transaction_type,
                "units": quantity,
                "price": price,
                "transaction_date": date_str,
            },
        )

        return int(result.lastrowid)

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE LOWER(item_name) = LOWER(:item_name)
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        AND q.total_amount > 0
        AND LOWER(q.quote_explanation) NOT LIKE '%error parsing%'
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


# Set up and load your env parameters and instantiate your model.
import os
import dotenv

dotenv.load_dotenv()
openai_api_key = os.getenv("UDACITY_OPENAI_API_KEY")

model = OpenAIServerModel(model_id = "gpt-4o-mini", api_base = "https://openai.vocareum.com/v1", api_key = openai_api_key)

"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""


# Tools for inventory agent

@tool
def inventory_specific_item(
    paper_type: str,
    as_of_date: Union[str, datetime],
) -> Dict:
    """
    Check the inventory level of a specific catalog item.

    Args:
        paper_type: Exact catalog item name.
        as_of_date: Inventory cutoff date in YYYY-MM-DD format.

    Returns:
        Dictionary containing the item name and current stock.
    """
    result = get_stock_level(paper_type, as_of_date)

    stock = (
        int(result.iloc[0]["current_stock"])
        if not result.empty
        else 0
    )

    return {
        "item_name": paper_type,
        "current_stock": stock,
    }

@tool
def Inventory_full(as_of_date: str) -> Dict[str, int]:

    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    return get_all_inventory(as_of_date)


# Tools for sales agent
@tool
def quoting_history(Key_word: List[str]) -> List[Dict]:
    """
    Get the quote history according to customer's request
    Args:
        Key_word: Keyword used in the Customer's request
    Return: 
        Matching quote history for those keywords
    """
    return search_quote_history(Key_word)

# Tools for Finance agent

@tool
def create_order(item_name: str, transaction_type: str,  quantity: int,  price: float,  date: Union[str, datetime]) -> int:
    """
    creates the Order and updates the database
    Args:
        item_name: Name of the item Ordered
        transaction_type: Either 'stock_orders' or 'sales'
        quantity: quantities ordered
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format. 
    Returns:
        ID: Newly created Order ID
    """
    return create_transaction(item_name,transaction_type,quantity,price,date)

@tool
def check_cash_balance(as_of_date : Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.
    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.
    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.
    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    return get_cash_balance(as_of_date)

@tool
def generate_report(as_of_date: Union[str, datetime])-> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    return generate_financial_report(as_of_date)

# Tool for purchase Agent


@tool
def check_delivery_time(
    input_date: str,
    quantity: int,
    required_delivery_date: str,
) -> Dict:
    """
    Calculate supplier delivery and deadline feasibility.

    Args:
        input_date: Request date in YYYY-MM-DD format.
        quantity: Shortage quantity.
        required_delivery_date: Customer deadline in YYYY-MM-DD format.

    Returns:
        Supplier delivery date and whether the deadline can be met.
    """
    supplier_date = get_supplier_delivery_date(input_date, quantity)

    can_meet = (
        datetime.fromisoformat(supplier_date)
        <= datetime.fromisoformat(required_delivery_date)
    )

    return {
        "supplier_delivery_date": supplier_date,
        "required_delivery_date": required_delivery_date,
        "can_meet_deadline": can_meet,
    }

@tool
def process_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    total_price: float,
    transaction_date: str,
) -> Dict:
    """
    Validate and create one financial transaction.

    Args:
        item_name: Exact catalog item name.
        transaction_type: Either sales or stock_orders.
        quantity: Number of units involved.
        total_price: Total transaction value.
        transaction_date: Transaction date in YYYY-MM-DD format.

    Returns:
        Dictionary containing transaction status, ID, and cash balance.
    """
    if quantity <= 0:
        return {
            "transaction_created": False,
            "transaction_id": None,
            "reason": "Quantity must be greater than zero.",
        }

    if total_price <= 0:
        return {
            "transaction_created": False,
            "transaction_id": None,
            "reason": "Transaction price must be greater than zero.",
        }

    cash = get_cash_balance(transaction_date)

    if transaction_type == "stock_orders" and total_price > cash:
        return {
            "transaction_created": False,
            "transaction_id": None,
            "cash_balance": cash,
            "reason": "Insufficient cash for the stock purchase.",
        }

    transaction_id = create_transaction(
        item_name=item_name,
        transaction_type=transaction_type,
        quantity=quantity,
        price=total_price,
        date=transaction_date,
    )

    updated_cash = get_cash_balance(transaction_date)

    return {
        "transaction_created": True,
        "transaction_type": transaction_type,
        "transaction_id": transaction_id,
        "cash_balance": updated_cash,
    }

# Set up your agents and create an orchestration agent that will manage them.

class InventoryManagementAgent(ToolCallingAgent):
    """Agent responsible for managing the Inventory"""
    def __init__(self, model):
        super().__init__(
            tools = [inventory_specific_item, Inventory_full],
            model = model,
            name = "inventory_Agent",
            description = ("Checks individual item stock levels, reviews the complete inventory, "
                "and determines whether available stock is sufficient to fulfill an order. "
                "When stock is insufficient, reports the available quantity and shortage."              
                "Check inventory using exactly the as-of date supplied by the orchestrator. "
                "Never replace, infer, or invent another date. "
                "Use inventory_specific_item first. Use Inventory_full only when the exact "
                "item name cannot be matched."

            ),
        )

class SalesAgent(ToolCallingAgent):
    """Agent responsible for understanding the quote, searching historical quote, and determine the pricing"""
    def __init__(self,model):
        super().__init__(
            tools = [quoting_history],
            model = model,
            name = "sales_Agent",
            description = (
                "Analyzes customer quote requests, searches historical quote records, "
                "determines competitive pricing, applies appropriate bulk discounts, "
                "and returns a clearly explained quote recommendation."
            ),
            max_steps = 5
        )

class PurchaseAgent(ToolCallingAgent):
    """Agent responsible for calculating supplier delivery feasibility."""

    def __init__(self, model):
        super().__init__(
            tools=[check_delivery_time],
            model=model,
            name="Purchasing_Agent",
            description=(
                "Use exactly the request date, shortage quantity, and customer "
                "deadline provided by the orchestrator. Call check_delivery_time "
                "exactly once. Do not invent or substitute dates or quantities. "
                "Return the tool result immediately."
            ),
            max_steps=3,
        )

class FinanceAgent(ToolCallingAgent):
    """Agent responsible for financial transactions and reporting."""

    def __init__(self, model):
        super().__init__(
            tools=[
                process_transaction,
                generate_report,
                check_cash_balance,
            ],
            model=model,
            name="Finance_Agent",
            description=(
                "Process transactions using the exact values supplied by the "
                "orchestrator. For a transaction request, call process_transaction "
                "exactly once and return its result immediately. Never invent or "
                "replace the transaction date. Use generate_report only when a "
                "financial report is explicitly requested."
            ),
            max_steps=2,
        )

class Orchestrator(ToolCallingAgent):
    """Orchestrator that coordinates the multi-agent order workflow."""

    def __init__(self, model):
        self.model = model
        self.purchase_manager = PurchaseAgent(model)
        self.finance_manager = FinanceAgent(model)
        self.sales_manager = SalesAgent(model)
        self.inventory_manager = InventoryManagementAgent(model)

        @tool
        def generate_sales_quote(customer_request: str) -> str:
            """
            Analyze a customer request and generate a quote using historical pricing.

            Args:
                customer_request: Complete customer request including the request date.

            Returns:
                Structured quote with catalog items, quantities, dates, pricing,
                and explanation.
            """
            prompt = f"""
            Analyze the following customer request:

            {customer_request}

            Valid catalog item names:

            {CATALOG_ITEM_NAMES}

            You must:

            1. Identify every requested product exactly as written.
            2. Map a product to a catalog item only when it is clearly the same product
            with descriptive wording removed.
            3. Do not substitute a different paper size, material, or product category.
            4. If no true catalog match exists, return ITEM_NAME: UNAVAILABLE and preserve
            the original requested product in ORIGINAL_ITEM.
            5. Identify the quantity for each item.
            6. Identify the request date.
            7. Identify the required delivery date.
            8. Use quoting_history to search relevant historical quotes.
            9. Generate competitive pricing.
            10. Apply a bulk discount only when justified.

            Do not invent catalog item names.

            Valid mappings:
            - colored paper assorted colors -> Colored paper
            - heavy cardstock white -> Cardstock
            - A4 glossy paper -> Glossy paper
            - printer paper -> Standard copy paper
            - decorative washi tape -> Decorative adhesive tape (washi tape)
            - poster board 24x36 -> Large poster paper (24x36 inches)
            - colorful construction paper -> Construction paper
            - sturdy cardstock -> Cardstock
            - cardstock in assorted colors -> Cardstock
            - paper napkins -> Paper napkins

            Invalid mappings:
            - A3 paper -> A4 paper
            - balloons -> any paper product
            - streamers -> Colored paper
            - glossy paper -> Letter-sized paper

            Return:

            Return one block for every requested item:

            ITEMS:
            ORIGINAL_ITEM: <customer wording>
            ITEM_NAME: <exact catalog item name or UNAVAILABLE>
            QUANTITY: <integer>
            UNIT_PRICE: <number or 0 when unavailable>
            LINE_TOTAL: <number or 0 when unavailable>
            DISCOUNTED_LINE_TOTAL: <number or 0 when unavailable>

            REQUEST_DATE: <YYYY-MM-DD>

            REQUIRED_DELIVERY_DATE: <YYYY-MM-DD or NOT_PROVIDED>

            SUBTOTAL: <number>

            DISCOUNT_PERCENT: <number>

            QUOTED_AMOUNT: <number>

            UNAVAILABLE_ITEMS: <comma-separated original items or NONE>

            QUOTE_EXPLANATION: <short explanation>

            LINE_TOTAL = UNIT_PRICE × QUANTITY.

            DISCOUNTED_LINE_TOTAL =
            LINE_TOTAL × (1 - DISCOUNT_PERCENT / 100).

            The sum of all available-item DISCOUNTED_LINE_TOTAL values must equal QUOTED_AMOUNT.

            Use historical quotes to recommend pricing.

            Historical quote results may contain invalid records where:
            - total_amount is -1
            - quote_explanation says "Error parsing response"

            Ignore those invalid records completely.

            Use only historical quotes with a positive total_amount.

            If no valid historical quote exists for a valid catalog item, use that item's
            catalog unit price or a clearly comparable historical unit price.

            If any item has no exact valid catalog match:

            ITEM_NAME: UNAVAILABLE
            UNIT_PRICE: 0
            LINE_TOTAL: 0
            DISCOUNTED_LINE_TOTAL: 0

            List it in UNAVAILABLE_ITEMS.

            Do not map an unavailable item to another product merely to complete the order.

            Never reject or stop processing a customer request only because historical
            quote data is missing or contains an invalid record.
            Call quoting_history only once per requested item.

            Do not return zero prices unless the historical quote genuinely indicates a free item.

            
            """

            return str(SalesAgent(self.model).run(prompt))

        @tool
        def check_order_inventory(
            item_name: str,
            quantity: int,
            request_date: Union[str, datetime],
        ) -> str:
            """
            Check whether inventory is sufficient for a proposed customer order.

            Args:
                item_name: Exact catalog item requested.
                quantity: Number of units requested.
                request_date: Customer request date in YYYY-MM-DD format.

            Returns:
                Current stock, sufficiency status, and shortage.
            """
            prompt = f"""
        Check inventory for this proposed order:

        Item: {item_name}
        Requested quantity: {quantity}
        As-of date: {request_date}

        Use the inventory tools to check the real database.

        Use exactly this item name and date. Do not invent another date.

        Return:

        ITEM_NAME: <item name>
        REQUESTED_QUANTITY: <integer>
        AVAILABLE_STOCK: <integer>
        SUFFICIENT_STOCK: <YES or NO>
        SHORTAGE: <integer>

        SHORTAGE must be 0 when inventory is sufficient.

        Do not estimate supplier delivery and do not create transactions.
        """

            return str(InventoryManagementAgent(self.model).run(prompt))

        @tool
        def check_supplier_filfillment(
            item_name: str,
            shortage: int,
            request_date: str,
            required_delivery_date: str,
        ) -> str:
            """
            Estimate supplier delivery when inventory is insufficient.

            Args:
                item_name: Paper item that needs replenishment.
                shortage: Additional units required.
                request_date: Customer request date in YYYY-MM-DD format.
                required_delivery_date: Customer deadline in YYYY-MM-DD format.

            Returns:
                Supplier delivery date and delivery feasibility.
            """
            prompt = f"""
            Inventory is insufficient for this order.

            Item: {item_name}
            Shortage quantity: {shortage}
            Request date: {request_date}
            Customer required delivery date: {required_delivery_date}

            Call the check_delivery_time tool exactly once with:

            input_date = {request_date}
            quantity = {shortage}
            required_delivery_date = {required_delivery_date}

            Use the values returned by the tool exactly as they are.
            Do not calculate the deadline yourself.

            input_date = {request_date}
            quantity = {shortage}
            required_delivery_date = {required_delivery_date}

            Use the boolean can_meet_deadline returned by the tool.

            Return:

            ITEM_NAME: <item name>
            SHORTAGE: <integer>
            SUPPLIER_DELIVERY_DATE: <YYYY-MM-DD>
            CAN_MEET_CUSTOMER_DEADLINE: <YES or NO>
            EXPLANATION: <short explanation>

            Do not create a transaction.
            """

            return str(PurchaseAgent(self.model).run(prompt))

        @tool
        def record_business_transaction(
            item_name: str,
            transaction_type: str,
            quantity: int,
            total_price: float,
            transaction_date: str,
        ) -> str:
            """
            Check finances and record a sales or stock-order transaction.

            Args:
                item_name: Paper item involved in the transaction.
                transaction_type: Either sales or stock_orders.
                quantity: Number of units involved.
                total_price: Total transaction amount.
                transaction_date: Transaction date in YYYY-MM-DD format.

            Returns:
                Financial status and transaction ID.
            """
            prompt = f"""
            Create exactly one transaction using these values:

            Item: {item_name}
            Transaction type: {transaction_type}
            Quantity: {quantity}
            Total price: {total_price}
            Transaction date: {transaction_date}

            Call process_transaction exactly once.

            Use exactly:
            - item_name = {item_name}
            - transaction_type = {transaction_type}
            - quantity = {quantity}
            - total_price = {total_price}
            - transaction_date = {transaction_date}

            Do not call generate_report.
            Do not change the date.
            Do not create the transaction more than once.
            Return the exact result from process_transaction.
            """

            return str(FinanceAgent(self.model).run(prompt))

        super().__init__(
            tools=[
                generate_sales_quote,
                check_order_inventory,
                check_supplier_filfillment,
                record_business_transaction,
            ],
            model=model,
            name="order_orchestrator",
            description=(
                "Coordinate customer quote requests and complete order fulfillment. "

                "Always call generate_sales_quote first. Before calling any other tool, "
                "read the UNAVAILABLE_ITEMS field returned by generate_sales_quote. "

                "If UNAVAILABLE_ITEMS is not NONE, reject the entire order immediately. "
                "Clearly identify the unavailable items. Do not call inventory, supplier, "
                "or transaction tools. Do not partially fulfill the order. "

                "If UNAVAILABLE_ITEMS is NONE, use only the exact ITEM_NAME values returned "
                "by generate_sales_quote. Never use ORIGINAL_ITEM values for inventory "
                "checks or financial transactions. Never rename, replace, or invent a "
                "catalog item after quote generation. "

                "For multi-item orders, process each item sequentially. Call "
                "check_order_inventory exactly once for every valid item. "

                "If inventory is sufficient, create exactly one sales transaction using "
                "the item's DISCOUNTED_LINE_TOTAL as total_price. "

                "If inventory is insufficient and SHORTAGE is greater than zero, call "
                "check_supplier_filfillment using the exact item name, shortage quantity, "
                "request date, and required delivery date. Never call supplier fulfillment "
                "when shortage is zero. "

                "Use the can_meet_deadline result returned by the supplier tool exactly as "
                "provided. If any supplier cannot meet the required delivery date, reject "
                "the entire order and do not create any transactions. "

                "If the supplier can meet the deadline, first create exactly one "
                "stock_orders transaction for the shortage quantity. Then create exactly "
                "one sales transaction for the full customer quantity. Return both the "
                "stock-order transaction ID and the sales transaction ID. "

                "Never create a transaction for an unavailable or non-catalog item. Never "
                "create a transaction with a zero or missing price. Never create duplicate "
                "transactions. "

                "Return the quoted amount, fulfillment or rejection decision, supplier "
                "delivery dates when relevant, stock-order transaction IDs, sales "
                "transaction IDs, unavailable items, or a clear rejection reason."
            ),
            max_steps=12,
        )

# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############
    orchestrator = Orchestrator(model)
    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        # response = call_your_multi_agent_system(request_with_date)
        response = orchestrator.run(
            f"""
            Process this customer request in this exact order:

            1. Call generate_sales_quote first.

            2. Read the UNAVAILABLE_ITEMS field returned by generate_sales_quote.

            3. If UNAVAILABLE_ITEMS is not NONE:
            - reject the entire order immediately;
            - clearly list the unavailable items;
            - do not call check_order_inventory;
            - do not call check_supplier_filfillment;
            - do not call record_business_transaction;
            - do not partially fulfill the order;
            - return a clear rejection reason.

            4. If UNAVAILABLE_ITEMS is NONE:
            - use only the exact ITEM_NAME values returned by generate_sales_quote;
            - never use ORIGINAL_ITEM values for inventory checks or transactions;
            - never rename, replace, or invent catalog items.

            5. Check each valid item exactly once using check_order_inventory.

            6. For every item with sufficient stock:
            - create exactly one sales transaction;
            - use DISCOUNTED_LINE_TOTAL as total_price.

            7. For every item with insufficient stock:
            - call check_supplier_filfillment only when SHORTAGE is greater than zero;
            - use the exact shortage, request date, and required delivery date.

            8. If any supplier cannot meet the customer deadline:
            - reject the entire order;
            - do not create any transactions for the order.

            9. If the supplier can meet the deadline:
            - first create one stock_orders transaction for the shortage quantity;
            - then create one sales transaction for the full customer quantity;
            - return both the stock_orders transaction ID and the sales transaction ID.

            10. Never create a transaction when:
                - ITEM_NAME is UNAVAILABLE;
                - the item is not an exact catalog item;
                - total_price is zero or missing;
                - the order has already been rejected.

            11. Return:
                - quoted amount;
                - fulfillment or rejection decision;
                - delivery date when supplier delivery was required;
                - sales transaction IDs;
                - stock-order transaction IDs;
                - unavailable items or rejection reason.
            Customer request:
            {request_with_date}
            """
            )

        response = str(response)

            # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
                {
                    "request_id": idx + 1,
                    "request_date": request_date,
                    "cash_balance": current_cash,
                    "inventory_value": current_inventory,
                    "response": response,
                }
            )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
