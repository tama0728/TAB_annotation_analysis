import json
from datetime import datetime
import difflib

def generate_changes_report():
    """Generate a detailed JSON report of all changes between original and exported files, ignoring provenance"""

    # Load files
    with open('personapii_tab_144_annotator4.jsonl', 'r') as f:
        original = [json.loads(line.strip()) for line in f if line.strip()]

    with open('pii_data_export_annot4.jsonl', 'r') as f:
        exported = [json.loads(line.strip()) for line in f if line.strip()]

    # Create lookups
    orig_by_id = {record['metadata']['data_id']: record for record in original}
    exp_by_id = {record['metadata']['data_id']: record for record in exported}

    # Initialize report structure
    report = {
        "metadata": {
            "comparison_timestamp": datetime.now().isoformat(),
            "original_file": "personapii_tab_144_annotator4.jsonl",
            "exported_file": "pii_data_export_annot4.jsonl",
            "total_records": len(original),
            "records_with_changes": 0,
            "ignored_fields": ["provenance"]
        },
        "summary": {
            "missing_metadata_fields": 0,
            "subject_count_changes": 0,
            "pii_annotation_changes": 0,
            "identical_text_content": 0,
            "description_changes": 0,
            "text_changes": 0
        },
        "changes_by_record": {}
    }

    identical_text_count = 0

    for data_id in orig_by_id.keys():
        orig = orig_by_id[data_id]
        exp = exp_by_id[data_id]

        record_changes = {
            "metadata_changes": {},
            "subject_count_change": None,
            "text_identical": orig['text'] == exp['text'],
            "text_changes": None,
            "subject_changes": []
        }

        has_changes = False

        # Check text identity and analyze differences
        if record_changes["text_identical"]:
            identical_text_count += 1
        else:
            # Analyze text differences
            orig_text = orig['text']
            exp_text = exp['text']
            
            # Use difflib to find differences
            diff = list(difflib.unified_diff(
                orig_text.splitlines(keepends=True),
                exp_text.splitlines(keepends=True),
                fromfile='original',
                tofile='exported',
                lineterm=''
            ))
            
            # Extract meaningful changes
            text_changes = {
                "original_length": len(orig_text),
                "exported_length": len(exp_text),
                "length_difference": len(exp_text) - len(orig_text),
                "line_differences": [],
                "character_changes": []
            }
            
            # Process unified diff
            for line in diff:
                if line.startswith('@@'):
                    continue
                elif line.startswith('---') or line.startswith('+++'):
                    continue
                elif line.startswith('-'):
                    text_changes["line_differences"].append({
                        "type": "removed",
                        "content": line[1:].rstrip()
                    })
                elif line.startswith('+'):
                    text_changes["line_differences"].append({
                        "type": "added", 
                        "content": line[1:].rstrip()
                    })
            
            # Find character-level differences using SequenceMatcher
            matcher = difflib.SequenceMatcher(None, orig_text, exp_text)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag != 'equal':
                    text_changes["character_changes"].append({
                        "type": tag,
                        "original_text": orig_text[i1:i2],
                        "exported_text": exp_text[j1:j2],
                        "original_position": i1,
                        "exported_position": j1
                    })
            
            record_changes["text_changes"] = text_changes
            has_changes = True
            report["summary"]["text_changes"] += 1

        # Check metadata changes (IGNORE provenance)
        orig_meta = orig['metadata']
        exp_meta = exp['metadata']

        for key in orig_meta:
            # SKIP provenance field
            if key == "provenance":
                continue

            if key not in exp_meta:
                record_changes["metadata_changes"][key] = {
                    "type": "missing",
                    "original_value": orig_meta[key]
                }
                has_changes = True
                report["summary"]["missing_metadata_fields"] += 1
            elif orig_meta[key] != exp_meta[key]:
                record_changes["metadata_changes"][key] = {
                    "type": "modified",
                    "original_value": orig_meta[key],
                    "new_value": exp_meta[key]
                }
                has_changes = True

        # Check for extra metadata in exported (still skip provenance)
        for key in exp_meta:
            if key == "provenance":
                continue
            if key not in orig_meta:
                record_changes["metadata_changes"][key] = {
                    "type": "added",
                    "new_value": exp_meta[key]
                }
                has_changes = True

        # Check subject count changes
        if len(orig['subjects']) != len(exp['subjects']):
            record_changes["subject_count_change"] = {
                "original": len(orig['subjects']),
                "exported": len(exp['subjects']),
                "difference": len(exp['subjects']) - len(orig['subjects'])
            }
            has_changes = True
            report["summary"]["subject_count_changes"] += 1

        # Compare subjects in detail
        orig_subjects = {s['id']: s for s in orig['subjects']}
        exp_subjects = {s['id']: s for s in exp['subjects']}

        for subject_id in set(orig_subjects.keys()) | set(exp_subjects.keys()):
            subject_change = {
                "subject_id": subject_id,
                "changes": {}
            }

            if subject_id not in orig_subjects:
                subject_change["changes"]["status"] = "added_in_exported"
                subject_change["changes"]["description"] = {
                    "exported": exp_subjects[subject_id]['description'],
                    "change_type": "added"
                }
                has_changes = True
                report["summary"]["description_changes"] += 1
            elif subject_id not in exp_subjects:
                subject_change["changes"]["status"] = "missing_in_exported"
                subject_change["changes"]["description"] = {
                    "original": orig_subjects[subject_id]['description'],
                    "change_type": "removed"
                }
                has_changes = True
                report["summary"]["description_changes"] += 1
            else:
                orig_subj = orig_subjects[subject_id]
                exp_subj = exp_subjects[subject_id]

                # Compare description
                if orig_subj['description'] != exp_subj['description']:
                    subject_change["changes"]["description"] = {
                        "original": orig_subj['description'],
                        "exported": exp_subj['description'],
                        "change_type": "modified"
                    }
                    has_changes = True
                    report["summary"]["description_changes"] += 1

                # Compare PIIs
                orig_piis = {pii['tag']: pii for pii in orig_subj['PIIs']}
                exp_piis = {pii['tag']: pii for pii in exp_subj['PIIs']}

                pii_changes = {}
                for tag in set(orig_piis.keys()) | set(exp_piis.keys()):
                    if tag not in orig_piis:
                        pii_changes[tag] = {
                            "type": "added",
                            "exported_value": exp_piis[tag]
                        }
                        has_changes = True
                    elif tag not in exp_piis:
                        pii_changes[tag] = {
                            "type": "removed",
                            "original_value": orig_piis[tag]
                        }
                        has_changes = True
                    else:
                        orig_pii = orig_piis[tag]
                        exp_pii = exp_piis[tag]

                        pii_field_changes = {}
                        for field in ['keyword', 'certainty', 'hardness']:
                            if orig_pii[field] != exp_pii[field]:
                                pii_field_changes[field] = {
                                    "original": orig_pii[field],
                                    "exported": exp_pii[field]
                                }
                                has_changes = True

                        if pii_field_changes:
                            pii_changes[tag] = {
                                "type": "modified",
                                "field_changes": pii_field_changes
                            }

                if pii_changes:
                    subject_change["changes"]["pii_changes"] = pii_changes
                    report["summary"]["pii_annotation_changes"] += 1

            if subject_change["changes"]:
                record_changes["subject_changes"].append(subject_change)

        if has_changes:
            report["changes_by_record"][data_id] = record_changes
            report["metadata"]["records_with_changes"] += 1

    report["summary"]["identical_text_content"] = identical_text_count

    # Save report
    with open('changes_report_no_provenance.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Changes report (ignoring provenance) generated: changes_report_no_provenance.json")
    print(f"Records with changes: {report['metadata']['records_with_changes']}/{report['metadata']['total_records']}")
    print(f"Records with identical text: {report['summary']['identical_text_content']}")

    # Generate summary statistics
    change_types = {
        "subject_count_changes": 0,
        "pii_modifications": 0,
        "turkey_to_turkiye": 0,
        "age_format_changes": 0,
        "occupation_changes": 0,
        "other_metadata_changes": 0,
        "description_changes": 0,
        "text_changes": 0
    }

    for data_id, changes in report["changes_by_record"].items():
        # Count non-provenance metadata changes
        if changes.get("metadata_changes"):
            change_types["other_metadata_changes"] += 1

        if changes.get("subject_count_change"):
            change_types["subject_count_changes"] += 1
            
        if changes.get("text_changes"):
            change_types["text_changes"] += 1

        # Count specific types of changes
        for subject_change in changes.get("subject_changes", []):
            # Count description changes
            if "description" in subject_change.get("changes", {}):
                change_types["description_changes"] += 1
            
            pii_changes = subject_change.get("changes", {}).get("pii_changes", {})
            for tag, pii_change in pii_changes.items():
                if pii_change.get("type") == "modified":
                    field_changes = pii_change.get("field_changes", {})

                    if tag == "AGE" and "keyword" in field_changes:
                        orig_age = field_changes["keyword"]["original"]
                        exp_age = field_changes["keyword"]["exported"]
                        if str(orig_age).isdigit() and "-" in str(exp_age):
                            change_types["age_format_changes"] += 1

                    if "keyword" in field_changes:
                        orig_val = str(field_changes["keyword"]["original"])
                        exp_val = str(field_changes["keyword"]["exported"])
                        if "Turkey" in orig_val and "Türkiye" in exp_val:
                            change_types["turkey_to_turkiye"] += 1

                    if tag in ["OCCUPATION", "POSITION"] and "keyword" in field_changes:
                        change_types["occupation_changes"] += 1

                    change_types["pii_modifications"] += 1

    # Save summary
    summary_report = {
        "file_comparison_summary": {
            "timestamp": datetime.now().isoformat(),
            "files_compared": {
                "original": "personapii_tab_144_annotator4.jsonl",
                "exported": "pii_data_export_annot4.jsonl"
            },
            "ignored_fields": ["provenance"],
            "record_counts": {
                "total_records": report["metadata"]["total_records"],
                "records_with_changes": report["metadata"]["records_with_changes"],
                "records_with_identical_text": report["summary"]["identical_text_content"]
            },
            "change_type_counts": change_types,
            "key_findings": [
                f"{change_types['subject_count_changes']} records have different subject counts",
                f"{change_types['description_changes']} subjects have description changes",
                f"{change_types['text_changes']} records have text content changes",
                f"{change_types['age_format_changes']} records have age format changes (single age → range)",
                f"{change_types['turkey_to_turkiye']} location changes from Turkey → Türkiye",
                f"{change_types['other_metadata_changes']} records have other metadata changes",
                f"Text content identical in {report['summary']['identical_text_content']} records",
                "Provenance field differences ignored as requested"
            ]
        }
    }

    with open('changes_summary_no_provenance.json', 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)

    print(f"Summary report (ignoring provenance) generated: changes_summary_no_provenance.json")

if __name__ == "__main__":
    generate_changes_report()