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
        SELECT COUNT(*) FROM businesses;
    """,
    
    "list_all_businesses": """
        SELECT name_en, category, contact_number, address
        FROM businesses
        LIMIT {limit};
    """,
}

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
        "extractor": lambda m: {"district": m.group(1), "limit": 10}
    },
    {
        "pattern": r"(?:in|near|at|located).+?(\w+).+tourist place",
        "template": "places_in_district",
        "extractor": lambda m: {"district": m.group(1), "limit": 10}
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
        "extractor": lambda m: {"district": m.group(1)}
    },
    {
        "pattern": r"(?:info|information|details?).+district.+(\w+)",
        "template": "district_by_name",
        "extractor": lambda m: {"district": m.group(1)}
    },
    
    # NEW: Filtered place patterns
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
        "extractor": lambda m: {"district": m.group(1)}
    },
    {
        "pattern": r"count.+places?.+(?:in|at)\s+(\w+)",
        "template": "count_places_in_district",
        "extractor": lambda m: {"district": m.group(1)}
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
    # CRITICAL FIX: Explicit pattern for "Show me all tourist places"
    {
        "pattern": r"(?:show|list|give|find|tell).+(?:me|us)?.+(?:all|every).+tourist places?",
        "template": "list_all_places",
        "params": {"limit": 20}
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

