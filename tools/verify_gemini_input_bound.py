#!/usr/bin/env python3
"""Inspect exact official SDK sources without importing SDK dependencies or using a network."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

SDK_COMMIT = 'c0e9c54915970948258226e565bde6ef6d5c0b94'
PINS = {
    'google/genai/_local_tokenizer_loader.py': '27f4781b8b2274e022eaf812e3bf4249dfe1e991',
    'google/genai/version.py': '4a55e2b75e7b52947f0b99373d03a0c0e98d2eb2',
}
MAPS = (
    '_GEMINI_MODELS_TO_TOKENIZER_NAMES',
    '_GEMINI_STABLE_MODELS_TO_TOKENIZER_NAMES',
    '_GEMINI_MODELS_TO_HUGGINGFACE_TOKENIZER_NAMES',
)


def inspect(sdk_root):
    trees = {}
    for name, expected in PINS.items():
        source = (sdk_root / name).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest()
        if actual != expected:
            raise ValueError('Official SDK blob mismatch: ' + name)
        trees[name] = ast.parse(source)
    loader = trees['google/genai/_local_tokenizer_loader.py']
    namespace = {'__builtins__': {'str': str, 'ValueError': ValueError}}
    for node in loader.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in MAPS:
                value = ast.literal_eval(node.value)
                if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
                    raise ValueError('Unexpected SDK map shape')
                namespace[name] = value
    if not all(name in namespace for name in MAPS):
        raise ValueError('SDK model-map definitions missing')
    function = next(node for node in loader.body if isinstance(node, ast.FunctionDef) and node.name == 'get_tokenizer_name')
    # Compile only the pinned, pure name lookup. Imports/download/cache/tokenizer code never runs.
    exec(compile(ast.Module(body=[function], type_ignores=[]), '<pinned-sdk-model-lookup>', 'exec'), namespace)
    lookup = namespace['get_tokenizer_name']
    controls = {model: lookup(model) for model in ('gemini-2.5-flash', 'gemini-3.5-flash')}
    try:
        tokenizer = lookup('gemini-3.8-flash')
    except ValueError:
        tokenizer = None
    version_tree = trees['google/genai/version.py']
    version = next(ast.literal_eval(node.value) for node in version_tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == '__version__' for target in node.targets))
    return {
        'status': 'BLOCKED_NO_VERIFIED_REQUEST_INPUT_BOUND',
        'sdk_repository': 'googleapis/python-genai', 'sdk_commit': SDK_COMMIT, 'sdk_version': version,
        'verified_git_blobs': PINS, 'target_model': 'gemini-3.8-flash',
        'target_tokenizer_name': tokenizer, 'target_supported_by_local_lookup': tokenizer is not None,
        'positive_lookup_controls': controls,
        'request_input_bound_certified': False,
        'sdk_imported': False, 'tokenizer_models_downloaded': False,
        'provider_calls': 0, 'credentials_read': False,
        'limitation': 'Even a supported local name alone would not certify provider framing or a complete billable input bound.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-root', required=True, type=Path)
    print(json.dumps(inspect(parser.parse_args().sdk_root), indent=2))
