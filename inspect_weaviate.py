"""
Inspect Weaviate database contents directly
"""
import weaviate

client = weaviate.connect_to_local(host="localhost", port=8080)

try:
    collection = client.collections.get("AmrutChatbotDocs")
    
    # Fetch all objects without filters
    print("\n" + "="*80)
    print("ALL OBJECTS IN AmrutChatbotDocs")
    print("="*80)
    
    response =collection.query.fetch_objects(limit=100)
    
    print(f"\nTotal objects: {len(response.objects)}\n")
    
    for i, obj in enumerate(response.objects):
        print(f"\n--- Object {i+1} ---")
        print(f"UUID: {obj.uuid}")
        print(f"Properties:")
        for key, value in obj.properties.items():
            if key == "chunk_text":
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")
    
    # Now try with namespace filter
    print("\n" + "="*80)
    print("OBJECTS WITH NAMESPACE='Scrobits'")
    print("="*80)
    
    from weaviate.classes.query import Filter
    response_filtered = collection.query.fetch_objects(
        limit=100,
        filters=Filter.by_property("namespace").equal("Scrobits")
    )
    
    print(f"\nFiltered objects: {len(response_filtered.objects)}\n")
    
    for i, obj in enumerate(response_filtered.objects):
        print(f"\n--- Filtered Object {i+1} ---")
        print(f"Namespace: {obj.properties.get('namespace')}")
        print(f"Source: {obj.properties.get('source')}")
        print(f"Text: {obj.properties.get('chunk_text', '')[:100]}...")

finally:
    client.close()

print("\n" + "="*80)
print("INSPECTION COMPLETE")
print("="*80)
