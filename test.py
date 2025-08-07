# Example 1: A medium-sized payer with a "cost-optimized" mindset
medium_payer_cost_optimized = get_azure_recommendations(subscriber_count=2500000, price_tolerance="cost-optimized")
print(f"Cost-Optimized Recommendations: {medium_payer_cost_optimized}")

# Example 2: A small payer that wants "performance-first"
small_payer_performance_first = get_azure_recommendations(subscriber_count=500000, price_tolerance="performance-first")
print(f"Performance-First Recommendations: {small_payer_performance_first}")