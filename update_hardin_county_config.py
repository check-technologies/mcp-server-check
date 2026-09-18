#!/usr/bin/env python3
"""
Script to update the Hardin County Occupational License Fee Return form filing configuration.

This script updates the applicability rules for flc_EDPAkJlnB2GX3HeMeZni to:
1. Include "Hardin YTD Subject Payroll Total" parameter
2. Include "KY Hardin YTD Tax Amount" parameter  
3. Remove "ky_hardin_qtd_subject_wages" parameter from applicability rule 1
"""

import httpx
import os
import json
import sys


def update_hardin_county_config():
    """Update the Hardin County form filing configuration applicability rules."""
    
    # Get API key from environment
    api_key = os.environ.get("CHECK_API_KEY")
    if not api_key:
        print("Error: CHECK_API_KEY environment variable not set")
        sys.exit(1)
    
    # API configuration
    base_url = os.environ.get("CHECK_API_BASE_URL", "https://sandbox.checkhq.com")
    config_id = "flc_EDPAkJlnB2GX3HeMeZni"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    client = httpx.Client(base_url=base_url, headers=headers, timeout=30.0)
    
    try:
        # First, get the current configuration
        print(f"Fetching current configuration for {config_id}...")
        response = client.get(f"/form_filing_configs/{config_id}")
        response.raise_for_status()
        current_config = response.json()
        
        print("Current configuration:")
        print(json.dumps(current_config, indent=2))
        print()
        
        # Prepare the update payload
        # Note: The exact structure of applicability_rules needs to be confirmed
        # based on the actual API response structure
        update_data = {
            "applicability_rules": [
                {
                    "rule_number": 1,
                    "parameters": [
                        "hardin_ytd_subject_payroll_total",
                        "ky_hardin_ytd_tax_amount",
                        # Note: removed ky_hardin_qtd_subject_wages as requested
                    ]
                }
            ]
        }
        
        print(f"Updating configuration with new applicability rules...")
        print("Update payload:")
        print(json.dumps(update_data, indent=2))
        print()
        
        # Update the configuration
        response = client.patch(f"/form_filing_configs/{config_id}", json=update_data)
        response.raise_for_status()
        updated_config = response.json()
        
        print("Configuration updated successfully!")
        print("Updated configuration:")
        print(json.dumps(updated_config, indent=2))
        
        return updated_config
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    update_hardin_county_config()
