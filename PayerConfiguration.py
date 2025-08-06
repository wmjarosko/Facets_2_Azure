# The main function to recommend Azure resources
def get_azure_recommendations(subscriber_count, price_tolerance):
    """
    Generates a list of recommended Azure resources based on payer size and price tolerance.
    """
    recommendations = {}
    
    # Logic for SQL Server
    if price_tolerance == "cost-optimized":
        if subscriber_count < 1000000:
            recommendations["sql_server"] = {"vm_series": "Standard_DS2_v2", "storage": "Standard_SSD"}
        else:
            recommendations["sql_server"] = {"vm_series": "Standard_DS4_v2", "storage": "Standard_SSD"}
    elif price_tolerance == "performance-first":
        if subscriber_count < 1000000:
            recommendations["sql_server"] = {"vm_series": "Standard_E8s_v3", "storage": "Premium_SSD"}
        else:
            recommendations["sql_server"] = {"vm_series": "Standard_E16s_v3", "storage": "Premium_SSD"}
    else:  # Balanced
        if subscriber_count < 1000000:
            recommendations["sql_server"] = {"vm_series": "Standard_D4s_v3", "storage": "Premium_SSD"}
        else:
            recommendations["sql_server"] = {"vm_series": "Standard_D8s_v3", "storage": "Premium_SSD"}

    # Logic for application servers, portals, etc. would follow a similar pattern here...
    
    return recommendations