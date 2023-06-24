import json
import os

from multiprocessing import cpu_count
from tqdm import tqdm

from utils.utils import *
from utils.rules import *

def _calculate_work_count(works, input_ext: str) -> int:
    if input_ext in TXT_SUFFIX:
        work_count = len(works)
    elif input_ext in JSONL_SUFFIX:
        work_count = 0
        for work in works:
            work_count += int(os.popen('wc -l %s' % work).read().split()[0])
    else:
        raise Exception(f"Invalid input extension {input_ext} is given in _calculate_work_count..\n")
    return work_count

def _prepare_tmp_files(input_ext: str, tmp_path: str, works: list, n_workers: int, work_count: int, source_tag: str):
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    tmp_file_line = int((work_count + n_workers) / n_workers)

    cnt, res, split = 0, [], 0
    if input_ext in TXT_SUFFIX:
        for work in tqdm(works, desc="Generating .tmp files"):
            cnt += 1
            try:
                with open(work, mode='r', encoding='utf-8') as fr:
                    res.append(fr.read())
            except Exception as ne:
                continue
            if cnt >= tmp_file_line:
                dump_data2jsonl(path=os.path.join(tmp_path, f'{split}.jsonl'), data=res, source_tag=source_tag)
                cnt, res, split = 0, [], split + 1
        if cnt > 0:
            dump_data2jsonl(path=os.path.join(tmp_path, f'{split}.jsonl'), data=res, source_tag=source_tag)
            cnt, res, split = 0, [], split + 1
    elif input_ext in JSONL_SUFFIX:
        for work in tqdm(works, desc="Generating .tmp files"):
            try:
                with open(work, mode='r', encoding='utf-8') as fr:
                    for line in fr:
                        cnt += 1
                        res.append(json.loads(line))
                        if cnt >= tmp_file_line:
                            dump_data2jsonl(path=os.path.join(tmp_path, f'{split}.jsonl'), data=res, source_tag=source_tag, text_key="text")
                            cnt, res, split = 0, [], split + 1
            except Exception as ne:
                print(f'bad file {work} for exception {ne}\n')
        if cnt > 0:
            dump_data2jsonl(path=os.path.join(tmp_path, f'{split}.jsonl'), data=res, source_tag=source_tag, text_key="text")
            cnt, res, split = 0, [], split + 1
    else:
        raise Exception(f"Unsupported extentsion type {source_tag} in _prepare_tmp_files..\n")

def prepare_parallel_works(input_path, output_path, input_ext='jsonl', source_tag='.tmp', n_process=-1):
    works = prepare_works(input_path=input_path, input_ext=input_ext)
    # Calculate work count
    work_count = _calculate_work_count(works=works, input_ext=input_ext)
    # Split work into pieces
    n_workers = n_process - 1 if n_process < 1 else cpu_count() - 1
    _prepare_tmp_files(input_ext=input_ext, tmp_path=output_path, works=works, n_workers=n_workers, work_count=work_count, source_tag=source_tag)