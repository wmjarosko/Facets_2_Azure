import requests
import json
import time

# A dynamic catalog of server types with their characteristics.
# The `server_count` field has been added for each server.
SERVER_CATALOG = [
    {
        "name": "SQL Server",
        "workload_type": "database",
        "description": "Primary database server for OLTP workloads.",
        "server_count": 1, # Default count
        "tiers": {
            "cost-optimized": {
                # Updated from Standard_DS2_v2 to a newer, supported SKU
                "small_payer_threshold": "Standard_D2as_v5", 
                "large_payer_threshold": "Standard_DS4_v2"   
            },
            "balanced": {
                "small_payer_threshold": "Standard_D4s_v3",
                "large_payer_threshold": "Standard_D8s_v3"
            },
            "performance-first": {
                "small_payer_threshold": "Standard_E8s_v3",
                "large_payer_threshold": "Standard_E16s_v3"
            }
        }
    },
    {
        "name": "Batch Processor",
        "workload_type": "application",
        "description": "Windows server for nightly batch jobs.",
        "server_count": 2, # Default count, often more than one for batch processing
        "tiers": {
            "cost-optimized": {
                "small_payer_threshold": "Standard_B2s",
                "large_payer_threshold": "Standard_B4ms"
            },
            "balanced": {
                "small_payer_threshold": "Standard_D2s_v3",
                "large_payer_threshold": "Standard_D4s_v3"
            },
            "performance-first": {
                "small_payer_threshold": "Standard_F4s_v2",
                "large_payer_threshold": "Standard_F8s_v2"
            }
        }
    },
    # We can add more server types here, like 'REST API Server', 'Portal Server', etc.
    # The structure remains consistent, making it easy to add new definitions.
]

def get_azure_recommendations(subscriber_count, price_tolerance):
    """
    Generates a list of recommended Azure resources dynamically from the catalog.
    """
    recommendations = {}
    
    # Iterate through our dynamic catalog to build the recommendations
    for server_type in SERVER_CATALOG:
        # Get the correct VM series based on price tolerance and subscriber count
        vm_series = ""
        tier = server_type["tiers"][price_tolerance]
        
        # Determine the size based on the subscriber threshold
        if subscriber_count < 1000000:
            vm_series = tier["small_payer_threshold"]
        else:
            vm_series = tier["large_payer_threshold"]
            
        recommendations[server_type["name"]] = {
            "vm_series": vm_series,
            "workload_type": server_type["workload_type"],
            "server_count": server_type["server_count"] # Add the server count to the recommendation
        }
    
    return recommendations

def fetch_all_vm_prices(region="eastus"):
    """
    Fetches all VM prices for a given region in a single API call.
    Returns a dictionary mapping SKU names to their hourly prices.
    """
    api_url = "https://prices.azure.com/api/retail/prices"
    
    filter_string = (
        f"serviceName eq 'Virtual Machines' and "
        f"armRegionName eq '{region}' and "
        f"priceType eq 'Consumption' and "
        f"unitOfMeasure eq '1 Hour'"
    )
    
    # We pass the filter for the initial request
    params = {"$filter": filter_string}
    all_prices = {}
    
    # The API is paginated, so we need to loop through all pages
    retries = 3
    for i in range(retries):
        try:
            # For the first request, use the filter. For subsequent requests, the URL already contains the filter.
            if i == 0:
                response = requests.get(api_url, params=params)
            else:
                response = requests.get(api_url)

            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get("Items", []):
                # We use the armSkuName as the key for easy lookup
                sku = item.get("armSkuName")
                price = item.get("retailPrice")
                if sku and price:
                    all_prices[sku] = price
            
            # Check for the next page link
            next_page_link = data.get("NextPageLink")
            if not next_page_link:
                break # Exit loop if there are no more pages

            api_url = next_page_link # Update URL for next iteration
            
        except requests.exceptions.RequestException as e:
            if i < retries - 1:
                print(f"Error fetching prices: {e}. Retrying in {2**(i+1)} seconds...")
                time.sleep(2**(i+1))
            else:
                print(f"Final attempt to fetch prices failed: {e}")
                break

    return all_prices

def get_total_estimated_monthly_cost(subscriber_count, price_tolerance, region="eastus", hours_in_month=730):
    """
    Calculates the total estimated monthly cost for an environment using a pre-fetched price list.
    """
    # Fetch all VM prices once before calculating
    all_prices = fetch_all_vm_prices(region)
    if not all_prices:
        print("\nFailed to fetch pricing data. Cannot calculate costs.")
        return 0.0

    recommendations = get_azure_recommendations(subscriber_count, price_tolerance)
    total_cost = 0.0
    
    print(f"\n--- Pricing Estimate for {subscriber_count} Subscribers ({price_tolerance.upper()}) ---")
    
    for server_name, config in recommendations.items():
        vm_sku = config["vm_series"]
        server_count = config["server_count"] # Get the new server count
        
        # Look up the hourly price in our dictionary
        hourly_price = all_prices.get(vm_sku)
        
        if hourly_price is not None:
            # Multiply by server count
            monthly_cost = hourly_price * hours_in_month * server_count
            total_cost += monthly_cost
            print(f"- {server_name} ({vm_sku}) x {server_count}: ${monthly_cost:.2f} per month")
        else:
            print(f"- Could not find price for {server_name} ({vm_sku}).")
    
    print(f"\nTOTAL ESTIMATED MONTHLY COST: ${total_cost:.2f}")
    return total_cost

# --- Example Usage ---
# A medium-sized payer with a "balanced" mindset
get_total_estimated_monthly_cost(subscriber_count=2500000, price_tolerance="balanced")

# A small payer with a "cost-optimized" mindset
get_total_estimated_monthly_cost(subscriber_count=500000, price_tolerance="cost-optimized")