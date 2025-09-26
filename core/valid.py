import json

with open('personapii_tab_144_annotator4.jsonl', 'r') as f:
    original = [json.loads(line) for line in f]

with open('pii_data_export_annot4.jsonl', 'r') as f:
    exported = [json.loads(line) for line in f]

print(len(original))
print(len(exported))

# check if the data is the same
# metadata data_id, number_of_subjects
# text
# subjects id, description



for ex in exported:
    if ex['metadata']['data_id'] not in [orig['metadata']['data_id'] for orig in original]:
        print(ex['metadata']['data_id'])
    
    # check if the data is the same
    if ex['data'] != [orig['data'] for orig in original if orig['metadata']['data_id'] == ex['metadata']['data_id']]:
        print(ex['metadata']['data_id'])

# check if the data is the same
for orig in original:
    if orig['metadata']['data_id'] not in [ex['metadata']['data_id'] for ex in exported]:
        print(orig['metadata']['data_id'])
    