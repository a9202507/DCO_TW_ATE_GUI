import pyvisa

# Create a resource manager
rm = pyvisa.ResourceManager()

# Scan for all connected VISA resources
resources = rm.list_resources()

print("Found {} instrument(s):".format(len(resources)))
print("-" * 50)

# Display all found resources
for resource in resources:
    print(resource)

# Optional: Query each instrument for identification
print("\n" + "=" * 50)
print("Attempting to query instruments for *IDN?:")
print("=" * 50)

for resource in resources:
    try:
        # Open connection to the instrument
        instrument = rm.open_resource(resource)
        # Query identification string
        idn = instrument.query('*IDN?')
        print(f"\n{resource}")
        print(f"  ID: {idn.strip()}")
        instrument.close()
    except Exception as e:
        print(f"\n{resource}")
        print(f"  Error: {str(e)}")