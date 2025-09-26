import json
import difflib
from datetime import datetime
import os
from typing import Dict, List, Any, Tuple


class JSONAnalyzer:
    """JSON 파일 비교 및 분석을 위한 클래스"""
    
    def __init__(self):
        self.ignored_fields = ["provenance"]
    
    def load_jsonl_file(self, file_path: str) -> List[Dict]:
        """JSONL 파일을 로드합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [json.loads(line.strip()) for line in f if line.strip()]
        except Exception as e:
            raise Exception(f"파일 로드 실패: {str(e)}")
    
    def analyze_text_differences(self, orig_text: str, exp_text: str) -> Dict[str, Any]:
        """텍스트 차이점을 분석합니다."""
        if orig_text == exp_text:
            return {"identical": True}
        
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
            "identical": False,
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
        
        return text_changes
    
    def compare_metadata(self, orig_meta: Dict, exp_meta: Dict) -> Dict[str, Any]:
        """메타데이터를 비교합니다."""
        metadata_changes = {}
        
        for key in orig_meta:
            # SKIP ignored fields
            if key in self.ignored_fields:
                continue
                
            if key not in exp_meta:
                metadata_changes[key] = {
                    "type": "missing",
                    "original_value": orig_meta[key]
                }
            elif orig_meta[key] != exp_meta[key]:
                metadata_changes[key] = {
                    "type": "modified",
                    "original_value": orig_meta[key],
                    "new_value": exp_meta[key]
                }
        
        # Check for extra metadata in exported
        for key in exp_meta:
            if key in self.ignored_fields:
                continue
            if key not in orig_meta:
                metadata_changes[key] = {
                    "type": "added",
                    "new_value": exp_meta[key]
                }
        
        return metadata_changes
    
    def compare_subjects(self, orig_subjects: List[Dict], exp_subjects: List[Dict]) -> Tuple[Dict, List[Dict]]:
        """Subject들을 비교합니다."""
        subject_count_change = None
        subject_changes = []
        
        # Check subject count changes
        if len(orig_subjects) != len(exp_subjects):
            subject_count_change = {
                "original": len(orig_subjects),
                "exported": len(exp_subjects),
                "difference": len(exp_subjects) - len(orig_subjects)
            }
        
        # Compare subjects in detail
        orig_subjects_dict = {s['id']: s for s in orig_subjects}
        exp_subjects_dict = {s['id']: s for s in exp_subjects}
        
        for subject_id in set(orig_subjects_dict.keys()) | set(exp_subjects_dict.keys()):
            subject_change = {
                "subject_id": subject_id,
                "changes": {}
            }
            
            if subject_id not in orig_subjects_dict:
                subject_change["changes"]["status"] = "added_in_exported"
                subject_change["changes"]["description"] = {
                    "exported": exp_subjects_dict[subject_id]['description'],
                    "change_type": "added"
                }
            elif subject_id not in exp_subjects_dict:
                subject_change["changes"]["status"] = "missing_in_exported"
                subject_change["changes"]["description"] = {
                    "original": orig_subjects_dict[subject_id]['description'],
                    "change_type": "removed"
                }
            else:
                orig_subj = orig_subjects_dict[subject_id]
                exp_subj = exp_subjects_dict[subject_id]
                
                # Compare description
                if orig_subj['description'] != exp_subj['description']:
                    subject_change["changes"]["description"] = {
                        "original": orig_subj['description'],
                        "exported": exp_subj['description'],
                        "change_type": "modified"
                    }
                
                # Compare PIIs
                pii_changes = self.compare_piis(orig_subj['PIIs'], exp_subj['PIIs'])
                if pii_changes:
                    subject_change["changes"]["pii_changes"] = pii_changes
            
            if subject_change["changes"]:
                subject_changes.append(subject_change)
        
        return subject_count_change, subject_changes
    
    def compare_piis(self, orig_piis: List[Dict], exp_piis: List[Dict]) -> Dict[str, Any]:
        """PII 어노테이션들을 비교합니다."""
        orig_piis_dict = {pii['tag']: pii for pii in orig_piis}
        exp_piis_dict = {pii['tag']: pii for pii in exp_piis}
        
        pii_changes = {}
        for tag in set(orig_piis_dict.keys()) | set(exp_piis_dict.keys()):
            if tag not in orig_piis_dict:
                # 새로 추가된 태그
                pii_changes[tag] = {
                    "type": "added",
                    "exported_value": exp_piis_dict[tag]
                }
            elif tag not in exp_piis_dict:
                # 삭제된 태그
                pii_changes[tag] = {
                    "type": "removed",
                    "original_value": orig_piis_dict[tag]
                }
            else:
                orig_pii = orig_piis_dict[tag]
                exp_pii = exp_piis_dict[tag]
                
                # 값이 0이나 공백인 경우를 체크
                orig_keyword = orig_pii.get('keyword', '')
                exp_keyword = exp_pii.get('keyword', '')
                
                # 원본이 0이나 공백이고 내보낸 것이 값이 있는 경우 -> 추가
                if self._is_empty_value(orig_keyword) and not self._is_empty_value(exp_keyword):
                    pii_changes[tag] = {
                        "type": "added",
                        "original_value": orig_pii,
                        "exported_value": exp_pii
                    }
                # 원본이 값이 있고 내보낸 것이 0이나 공백인 경우 -> 삭제
                elif not self._is_empty_value(orig_keyword) and self._is_empty_value(exp_keyword):
                    pii_changes[tag] = {
                        "type": "removed",
                        "original_value": orig_pii,
                        "exported_value": exp_pii
                    }
                else:
                    # 일반적인 필드 변경사항 체크
                    pii_field_changes = {}
                    for field in ['keyword', 'certainty', 'hardness']:
                        if orig_pii[field] != exp_pii[field]:
                            pii_field_changes[field] = {
                                "original": orig_pii[field],
                                "exported": exp_pii[field]
                            }
                    
                    if pii_field_changes:
                        pii_changes[tag] = {
                            "type": "modified",
                            "field_changes": pii_field_changes
                        }
        
        return pii_changes
    
    def _is_empty_value(self, value) -> bool:
        """값이 0, 공백, None인지 확인합니다."""
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == '' or value.strip() == '0'
        if isinstance(value, (int, float)):
            return value == 0
        return False
    
    def analyze_files(self, original_file: str, exported_file: str) -> Dict[str, Any]:
        """두 JSONL 파일을 비교 분석합니다."""
        # Load files
        original = self.load_jsonl_file(original_file)
        exported = self.load_jsonl_file(exported_file)
        
        # Create lookups
        orig_by_id = {record['metadata']['data_id']: record for record in original}
        exp_by_id = {record['metadata']['data_id']: record for record in exported}
        
        # Initialize report structure
        report = {
            "metadata": {
                "comparison_timestamp": datetime.now().isoformat(),
                "original_file": os.path.basename(original_file),
                "exported_file": os.path.basename(exported_file),
                "total_records": len(original),
                "records_with_changes": 0,
                "ignored_fields": self.ignored_fields
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
            if data_id not in exp_by_id:
                continue
                
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
                text_changes = self.analyze_text_differences(orig['text'], exp['text'])
                record_changes["text_changes"] = text_changes
                has_changes = True
                report["summary"]["text_changes"] += 1
            
            # Check metadata changes
            metadata_changes = self.compare_metadata(orig['metadata'], exp['metadata'])
            if metadata_changes:
                record_changes["metadata_changes"] = metadata_changes
                has_changes = True
                report["summary"]["missing_metadata_fields"] += len([k for k, v in metadata_changes.items() if v["type"] == "missing"])
            
            # Check subject changes
            subject_count_change, subject_changes = self.compare_subjects(orig['subjects'], exp['subjects'])
            if subject_count_change:
                record_changes["subject_count_change"] = subject_count_change
                has_changes = True
                report["summary"]["subject_count_changes"] += 1
            
            if subject_changes:
                record_changes["subject_changes"] = subject_changes
                has_changes = True
                report["summary"]["description_changes"] += len([s for s in subject_changes if "description" in s["changes"]])
                report["summary"]["pii_annotation_changes"] += len([s for s in subject_changes if "pii_changes" in s["changes"]])
            
            if has_changes:
                report["changes_by_record"][data_id] = record_changes
                report["metadata"]["records_with_changes"] += 1
        
        report["summary"]["identical_text_content"] = identical_text_count
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str) -> None:
        """분석 결과를 JSON 파일로 저장합니다."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
