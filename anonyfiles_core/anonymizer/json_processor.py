# anonyfiles_cli/anonymizer/json_processor.py

import json
import logging
from pathlib import Path
from typing import List, Any, Optional, Tuple
import aiofiles

from .base_processor import BaseProcessor

# from .utils import apply_positional_replacements # Probablement plus nécessaire ici

logger = logging.getLogger(__name__)


class JsonProcessor(BaseProcessor):
    def __init__(self) -> None:
        self._original_json: Any = None
        self._value_paths: List[List[Any]] = []
        self._key_paths: List[Tuple[List[Any], str]] = []

    def _traverse(
        self,
        node: Any,
        path: List[Any],
        collect_all: bool,
        values: List[str],
        target_keys: Optional[set],
        anonymize_keys: bool,
    ) -> None:
        """Recursively collect values and key names from the JSON tree."""
        if isinstance(node, dict):
            for k, v in node.items():
                if anonymize_keys:
                    # Track keys for anonymization
                    self._key_paths.append((path, k))
                    values.append(str(k))

                next_collect = collect_all or (target_keys and k in target_keys)

                if isinstance(v, (dict, list)):
                    self._traverse(
                        v, path + [k], next_collect, values, target_keys, anonymize_keys
                    )
                else:
                    if next_collect or target_keys is None:
                        self._value_paths.append(path + [k])
                        values.append(str(v))
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                if isinstance(item, (dict, list)):
                    self._traverse(
                        item,
                        path + [idx],
                        collect_all,
                        values,
                        target_keys,
                        anonymize_keys,
                    )
                else:
                    if collect_all or target_keys is None:
                        self._value_paths.append(path + [idx])
                        values.append(str(item))
        else:
            if collect_all or target_keys is None:
                self._value_paths.append(path)
                values.append(str(node))

    def extract_blocks(
        self,
        input_path: Path,
        *,
        anonymize_keys: bool = False,
        target_keys: Optional[List[str]] = None,
        **kwargs,
    ) -> List[str]:
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                self._original_json = json.load(f)
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error("Erreur lors de la lecture de %s: %s", input_path, e)
            self._original_json = None
            return []

        self._value_paths = []
        self._key_paths = []
        collected_values: List[str] = []
        keys_set = set(target_keys) if target_keys else None
        self._traverse(
            self._original_json, [], False, collected_values, keys_set, anonymize_keys
        )
        return collected_values

    async def extract_blocks_async(
        self,
        input_path: Path,
        *,
        anonymize_keys: bool = False,
        target_keys: Optional[List[str]] = None,
        **kwargs,
    ) -> List[str]:
        try:
            async with aiofiles.open(input_path, "r", encoding="utf-8") as f:
                self._original_json = json.loads(await f.read())
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error("Erreur lors de la lecture de %s: %s", input_path, e)
            self._original_json = None
            return []

        self._value_paths = []
        self._key_paths = []
        collected_values: List[str] = []
        keys_set = set(target_keys) if target_keys else None
        self._traverse(
            self._original_json, [], False, collected_values, keys_set, anonymize_keys
        )
        return collected_values

    def reconstruct_and_write_anonymized_file(
        self,
        output_path: Path,
        final_processed_blocks: List[str],
        original_input_path: Path,
        **kwargs,
    ) -> None:
        if self._original_json is None:
            with open(original_input_path, "r", encoding="utf-8") as f:
                self._original_json = json.load(f)

        anonymized_json = json.loads(json.dumps(self._original_json))

        def get_parent(obj: Any, path: List[Any]) -> Tuple[Any, Any]:
            cur = obj
            for p in path[:-1]:
                cur = cur[p]
            return cur, path[-1]

        index = 0
        # Replace values
        for path in self._value_paths:
            if index >= len(final_processed_blocks):
                break
            parent, key = get_parent(anonymized_json, path)
            parent[key] = final_processed_blocks[index]
            index += 1

        # Replace keys
        for parent_path, old_key in self._key_paths:
            if index >= len(final_processed_blocks):
                break
            parent = anonymized_json
            for p in parent_path:
                parent = parent[p]
            new_key = final_processed_blocks[index]
            index += 1
            parent[new_key] = parent.pop(old_key)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fout:
            json.dump(anonymized_json, fout, indent=2, ensure_ascii=False)

    async def reconstruct_and_write_anonymized_file_async(
        self,
        output_path: Path,
        final_processed_blocks: List[str],
        original_input_path: Path,
        **kwargs,
    ) -> None:
        if self._original_json is None:
            async with aiofiles.open(original_input_path, "r", encoding="utf-8") as f:
                self._original_json = json.loads(await f.read())

        anonymized_json = json.loads(json.dumps(self._original_json))

        def get_parent(obj: Any, path: List[Any]) -> Tuple[Any, Any]:
            cur = obj
            for p in path[:-1]:
                cur = cur[p]
            return cur, path[-1]

        index = 0
        for path in self._value_paths:
            if index >= len(final_processed_blocks):
                break
            parent, key = get_parent(anonymized_json, path)
            parent[key] = final_processed_blocks[index]
            index += 1

        for parent_path, old_key in self._key_paths:
            if index >= len(final_processed_blocks):
                break
            parent = anonymized_json
            for p in parent_path:
                parent = parent[p]
            new_key = final_processed_blocks[index]
            index += 1
            parent[new_key] = parent.pop(old_key)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        json_str = json.dumps(anonymized_json, indent=2, ensure_ascii=False)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as fout:
            await fout.write(json_str)

    # Ancienne méthode replace_entities (maintenant redondante pour le flux principal)
    # def replace_entities(self, input_path, output_path, replacements, entities_per_block_with_offsets):
    #     raise DeprecationWarning("JsonProcessor.replace_entities est obsolète.")
