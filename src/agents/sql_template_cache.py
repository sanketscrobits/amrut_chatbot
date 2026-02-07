"""
SQL Template Caching System
Provides fast SQL generation for common query patterns.
"""

import re
from typing import Dict, Optional

# EXPANDED: Template definitions (5 → 15+ templates)
SQL_TEMPLATES = {
    # Original templates
    "list_all_places": """
        SELECT name_en, name_mr, description_en, address, lat, lng, image_url
        FROM tourist_places
        LIMIT {limit};
    """,
    
    "places_in_district": """
        SELECT tp.name_en, tp.name_mr, tp.description_en, tp.address, tp.lat, tp.lng, tp.image_url
        FROM tourist_places AS tp
        JOIN districts AS d ON tp.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%'
        LIMIT {limit};
    """,
    
    "count_all_places": """
        SELECT COUNT(*) FROM tourist_places;
    """,
    
    "count_districts": """
        SELECT COUNT(*) FROM districts;
    """,
    
    "top_n_places": """
        SELECT name_en, name_mr, description_en, address, image_url
        FROM tourist_places
        LIMIT {limit};
    """,
    
    # NEW: District queries
    "list_all_districts": """
        SELECT name_en, name_mr, lat, lng
        FROM districts
        ORDER BY name_en
        LIMIT {limit};
    """,
    
    "district_by_name": """
        SELECT id, name_en, name_mr, lat, lng
        FROM districts
        WHERE name_en ILIKE '%{district}%'
        LIMIT 1;
    """,
    
    # NEW: Filtered place queries
    "places_with_description": """
        SELECT name_en, name_mr, description_en, address, image_url
        FROM tourist_places
        WHERE description_en IS NOT NULL AND description_en != ''
        LIMIT {limit};
    """,
    
    "places_with_images": """
        SELECT name_en, description_en, address, image_url
        FROM tourist_places
        WHERE image_url IS NOT NULL AND image_url != ''
        LIMIT {limit};
    """,
    
    # NEW: Count queries
    "count_places_in_district": """
        SELECT COUNT(*) as count
        FROM tourist_places tp
        JOIN districts d ON tp.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%';
    """,
    
    # NEW: Analytics queries
    "district_with_most_places": """
        SELECT d.name_en, d.name_mr, COUNT(tp.id) as place_count
        FROM districts d
        LEFT JOIN tourist_places tp ON d.id = tp.district_id
        GROUP BY d.id, d.name_en, d.name_mr
        ORDER BY place_count DESC
        LIMIT 1;
    """,
    
    "districts_with_places": """
        SELECT d.name_en, d.name_mr, COUNT(tp.id) as place_count
        FROM districts d
        INNER JOIN tourist_places tp ON d.id = tp.district_id
        GROUP BY d.id, d.name_en, d.name_mr
        HAVING COUNT(tp.id) > 0
        ORDER BY place_count DESC;
    """,
    
    # NEW: Business queries
    "count_all_businesses": """
        SELECT COUNT(*) FROM local_businesses;
    """,
    
    "list_all_businesses": """
        SELECT name_en, description_en, address
        FROM local_businesses
        LIMIT {limit};
    """,

    # NEW: Detailed Templates for CSV Analysis
    "get_district_population": """
        SELECT name_en, population
        FROM districts
        WHERE name_en ILIKE '%{district}%'
        LIMIT 1;
    """,
    "get_best_time_visit_district": """
        SELECT name_en, best_time_to_visit_en
        FROM districts
        WHERE name_en ILIKE '%{district}%'
        LIMIT 1;
    """,
    "get_place_entry_fee": """
        SELECT name_en, entry_fee
        FROM tourist_places
        WHERE name_en ILIKE '%{place}%'
        LIMIT 1;
    """,
    "get_place_hours": """
        SELECT name_en, opening_hours_en
        FROM tourist_places
        WHERE name_en ILIKE '%{place}%'
        LIMIT 1;
    """,
    "get_place_description": """
        SELECT name_en, description_en
        FROM tourist_places
        WHERE name_en ILIKE '%{place}%'
        LIMIT 1;
    """,
    "list_services_in_district": """
        SELECT es.name, es.phone, es.address, es.available_24_7
        FROM emergency_services es
        JOIN districts d ON es.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%' AND es.service_type ILIKE '%{service_type}%'
        LIMIT 10;
    """,
    "get_service_contact": """
        SELECT name, phone, address
        FROM emergency_services
        WHERE name ILIKE '%{name}%'
        LIMIT 1;
    """,
    "list_businesses_in_district": """
        SELECT b.name_en, b.description_en, b.address, b.phone
        FROM local_businesses b
        JOIN districts d ON b.district_id = d.id
        WHERE d.name_en ILIKE '%{district}%'
             AND (b.name_en ILIKE '%{category}%' OR b.description_en ILIKE '%{category}%')
        LIMIT 10;
    """,
    "get_business_contact": """
        SELECT name_en, phone, email, address
        FROM local_businesses
        WHERE name_en ILIKE '%{name}%'
        LIMIT 1;
    """,
}

# Helper to assist with singularization
def singularize(word):
    """
    Very basic singularization for our specific domain keywords.
    """
    word = word.strip("?.! ").lower() # Strip punctuation and lowercase
    
    # Custom mappings based on DB inspection
    mappings = {
        "hospitals": "Hospital",
        "hospital": "Hospital",
        "pharmacies": "Pharmacy",
        "pharmacy": "Pharmacy",
        "police stations": "Police",  # DB has 'Police'
        "police station": "Police",
        "police": "Police",
        "public toilets": "Public Toilet",
        "public toilet": "Public Toilet",
        "hotels": "Hotel",
        "hotel": "Hotel",
        "restaurants": "Restaurant",
        "restaurant": "Restaurant",
        "taxis": "Taxi",
        "taxi": "Taxi"
    }
    
    if word in mappings:
        return mappings[word]
        
    # Default stripping 's' if not found (basic fallback)
    if word.endswith('s') and word[:-1] in mappings.values(): # e.g. Forts -> Fort (if we had Fort)
         pass # Logic here is tricky without full dictionary. 
    
    # For now, just return title case if not in mapping, or strip 's' if it looks like a simple plural
    if word.endswith('s'):
        return word[:-1].title()
        
    return word.title()


# EXPANDED: Pattern matchers (6 → 20+ patterns)
QUERY_PATTERNS = [
    # Original patterns
    {
        "pattern": r"(?:show|list|give|find).+(?:all|every).+(?:tourist place|attraction|monument|heritage|site|sightseeing)",
        "template": "list_all_places",
        "params": {"limit": 10}
    },
    {
        "pattern": r"tourist place.+(?:in|near|at|located).+?(\w+)",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! "), "limit": 10}
    },
    {
        "pattern": r"(?:in|near|at|located).+?(\w+).+tourist place",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! "), "limit": 10}
    },
    {
        "pattern": r"(?:how many|count|total|number).+(?:tourist place|attraction|monument|place|site)",
        "template": "count_all_places",
        "params": {}
    },
    {
        "pattern": r"how many.+district",
        "template": "count_districts",
        "params": {}
    },
    {
        "pattern": r"(?:top|first)\s+(\d+).+tourist place",
        "template": "top_n_places",
        "extractor": lambda m: {"limit": int(m.group(1))}
    },
    
    # NEW: District query patterns
    {
        "pattern": r"(?:show|list|give).+(?:all|every).+districts?",
        "template": "list_all_districts",
        "params": {"limit": 36}
    },
    {
        "pattern": r"(?:show|find|get).+district.+(?:named?|called)\s+(\w+)",
        "template": "district_by_name",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:info|information|details?).+district.+(\w+)",
        "template": "district_by_name",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    
    # NEW: Filtered place patterns
    {
        "pattern": r"(?:show|list|find).*(?:forts?|monuments?|temples?|museums?|places?).+(?:in|at|of|near)\s+(\w+)",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! "), "limit": 10}
    },
    {
        "pattern": r"places?.+(?:with|having|contains?).+(?:description|detail|info)",
        "template": "places_with_description",
        "params": {"limit": 10}
    },
    {
        "pattern": r"places?.+(?:with|having).+(?:image|photo|picture)",
        "template": "places_with_images",
        "params": {"limit": 10}
    },
    
    # NEW: Count patterns
    {
        "pattern": r"how many.+places?.+(?:in|at|near)\s+(\w+)",
        "template": "count_places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"count.+places?.+(?:in|at)\s+(\w+)",
        "template": "count_places_in_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },

    # NEW: Detailed Templates for CSV Analysis (Population, Best Time, Etc)
    {
        "pattern": r"(?:what is the\s+)?population of (.+)",
        "template": "get_district_population",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"(?:tell me about|info on|details of)\s+(.+) district",
        "template": "get_district_description",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"best time to visit (.+)",
        "template": "get_best_time_visit_district",
        "extractor": lambda m: {"district": m.group(1).strip("?.! ")}
    },
    
    # Places details
    {
        "pattern": r"entry fee (?:for|of) (.+)",
        "template": "get_place_entry_fee",
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"opening hours (?:of|for) (.+)",
        "template": "get_place_hours", 
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    {
        "pattern": r"tell me about (.+) (?:fort|temple|museum|place)",
        "template": "get_place_description",
        "extractor": lambda m: {"place": m.group(1).strip("?.! ")}
    },
    
    # Emergency
    {
        "pattern": r"(hospitals?|pharmacies|police stations?|police).*(?:in|at|near)\s+(.+)",
        "template": "list_services_in_district",
        "extractor": lambda m: {"service_type": singularize(m.group(1)), "district": m.group(2).strip("?.! ")}
    },
    {
        "pattern": r"emergency.*(?:contact|number|phone|helpline).*(?:for|of)\s+(.+)",
        "template": "get_service_contact",
        "extractor": lambda m: {"name": m.group(1).strip("?.! ")}
    },
    
    # Businesses
    {
        "pattern": r"(hotels?|restaurants?|taxis?|lodges?).*(?:in|at|near)\s+(.+)",
        "template": "list_businesses_in_district",
        "extractor": lambda m: {"category": singularize(m.group(1)), "district": m.group(2).strip("?.! ")}
    },
     {
        "pattern": r"(?:contact|phone).*(?:number|details).*(?:for|of)\s+(.+)",
        "template": "get_business_contact",
        "extractor": lambda m: {"name": m.group(1).strip("?.! ")}
    },
    # CRITICAL FIX: Explicit pattern for "Show me all tourist places"
    {
        "pattern": r"(?:show|list|give|find|tell).+(?:me|us)?.+(?:all|every).+tourist places?",
        "template": "list_all_places",
        "params": {"limit": 20}
    },
    
    # NEW: Analytics patterns
    {
        "pattern": r"(?:which|what).+district.+(?:most|highest|maximum).+places?",
        "template": "district_with_most_places",
        "params": {}
    },
    {
        "pattern": r"district.+(?:most|maximum).+tourist",
        "template": "district_with_most_places",
        "params": {}
    },
    {
        "pattern": r"(?:which|what).+districts?.+(?:have|with).+places?",
        "template": "districts_with_places",
        "params": {}
    },
    {
        "pattern": r"(?:show|list).+districts?.+tourist",
        "template": "districts_with_places",
        "params": {}
    },
    
    {
        "pattern": r"(?:how many|count|total).+business",
        "template": "count_all_businesses",
        "params": {}
    },
    {
        "pattern": r"(?:show|list|give|find).+(?:all|every).+business",
        "template": "list_all_businesses",
        "params": {"limit": 10}
    },
]

def get_sql_from_template(query: str) -> Optional[str]:
    """
    Try to match query to a template.
    Returns SQL string if match found, None otherwise.
    """
    query_lower = query.lower()
    
    for pattern_config in QUERY_PATTERNS:
        match = re.search(pattern_config["pattern"], query_lower, re.IGNORECASE)
        
        if match:
            template_name = pattern_config["template"]
            template = SQL_TEMPLATES[template_name]
            
            # Extract parameters
            if "extractor" in pattern_config:
                try:
                    params = pattern_config["extractor"](match)
                except Exception:
                    # If extraction fails, skip this pattern
                    continue
            else:
                params = pattern_config.get("params", {})
            
            # Substitute parameters
            sql = template.format(**params)
            
            print(f"✅ SQL Template Cache HIT: {template_name}")
            return sql.strip()
    
    print(f"❌ SQL Template Cache MISS: Falling back to LLM generation")
    return None
