from utils.settings import *
from utils.parallel import prepare_parallel_works, process_parallel_works
from utils.rules import *
from utils.dumper import *
from utils.cleaner import *
from utils.filter import *
from utils.debugger import *
from utils.extractor import *

from tqdm import tqdm

from utils.utils import prepare_works
from utils.debugger import log_text

import os   

def process_work_mult_threads(work_path: str, output_path: str, extract_module: Extractor, clean_module: Cleaner, filter_module: Filter, parallel_paras, text_key: str, debugger_module: Debugger=None):
    process_parallel_works(work_path, output_path, extract_module, clean_module, filter_module, parallel_paras, text_key, debugger_module)

def process_work_single_thread(work_path: str, output_path: str, extract_module: Extractor, clean_module: Cleaner, filter_module: Filter, text_key: str="content", debugger_module: Debugger=None):
    if not os.path.exists(output_path): os.makedirs(output_path, exist_ok=True)
    for file in tqdm(prepare_works(work_path), desc='Process work single thread'):
        filename = os.path.basename(file)
        nwork_in = os.path.join(work_path, file)
        nwork_out = os.path.join(output_path, filename)
        log_text(f"work_in_path: {nwork_in}, work_out_path: {nwork_out}")
        assert(nwork_in != nwork_out)
        try:
            with open(nwork_in, mode='r', encoding='utf-8') as fr, open(nwork_out, mode='w', encoding='utf-8') as fw:
                for line in fr:
                    nrecord = json.loads(line)
                    if debugger_module is not None:
                        debugger_module.debug_single_text(nrecord[text_key])
                    text = process_single_text(nrecord[text_key], extract_module, clean_module, filter_module)
                    if text != "":
                        nrecord['text'] = text
                        fw.write(json.dumps(nrecord, ensure_ascii=False) + '\n')
        except Exception as ne:
            print(f"Bad work {nwork_in} for Exception {ne}")

def process_single_text(text: str, extract_module: Extractor, clean_module: Cleaner, filter_module: Filter) -> str:
    '''
    Return "" (an empty string) means the text is Filtered.
    Else return an extracted and cleaned module
    '''
    text = extract_module.extract(text)
    if filter_module.filter_single_text(text):
        return ""
    text = clean_module.clean_single_text(text)
    if filter_module.filter_single_text(text):
        return ""    
    return text

def process_work(conf: Settings):
    settings = conf.settings
    input_path, input_ext, input_text_key, output_path, output_source_value = settings['input_path'], settings['input_ext'], settings['input_text_key'], settings['output_path'], settings['output_source_value']

    if settings['if_debug']:
        debugger_module = Debugger(settings)
    else:
        debugger_module = None

    if settings['if_filter'] or settings['if_clean']:
        # regularize extension of input file 
        if settings['if_parallel']:
            parallel_paras = settings['parallel_paras']
            # todo: chunk_size
            work_path = os.path.join(output_path, '.tmp')
            prepare_parallel_works(
                input_path=input_path, 
                output_path=work_path, 
                input_ext=input_ext, 
                source_tag=output_source_value,
                n_process= parallel_paras['n_process'])
        else:
            work_path = os.path.join(output_path, '.tmp')
            if input_ext in TXT_SUFFIX:
                dump_txts2jsonl(
                    input_path=input_path, 
                    output_path=work_path, 
                    keep_text_only=False,
                    source_tag=output_source_value
                )
            elif input_ext in JSONL_SUFFIX:
                dump_jsonls2jsonl(
                    input_path=input_path, 
                    output_path=work_path, 
                    keep_text_only=False,
                    source_tag=output_source_value
                )
        
        # load settings for modules
        if settings['if_debug']: debugger_module = Debugger(settings)
        else: debugger_module = None
        extract_module = Extractor(setting=settings)
        clean_module = Cleaner(setting=settings)
        filter_module = Filter(setting=settings)

        # generate debugger report
        if settings['if_debug']:
            debugger_worklist = prepare_works(work_path)
            for file in debugger_worklist:
                with open(file, mode='r', encoding='utf-8') as fr:
                    cnt = 0
                    for line in fr:
                        cnt += 1
                        text = json.loads(line)[input_text_key]
                        debugger_module.debug_single_text(text)
                        if cnt >= debugger_module.sample_num:
                            break
            debugger_module.debug_params_report()

        # do work and calculate work statistics
        log_text(f"Parallel Setting: {settings['if_parallel']}")
        if settings['if_parallel']:
            process_work_mult_threads(
                work_path=work_path, 
                output_path=os.path.join(output_path, '.cleaned'), 
                extract_module=extract_module, 
                clean_module=clean_module, 
                filter_module=filter_module, 
                parallel_paras=parallel_paras,
                text_key=input_text_key,
            )
            dump_jsonls2jsonl(
                input_path=os.path.join(output_path, '.cleaned'),
                output_path=os.path.join(output_path, 'out'),
                keep_text_only=True,
                source_tag=output_source_value
            )
            log_text(f"Final data dir: {os.path.join(output_path, 'out')}")
        else:
            process_work_single_thread(
                work_path=work_path, 
                output_path=os.path.join(output_path, '.cleaned'), 
                extract_module=extract_module, 
                clean_module=clean_module, 
                filter_module=filter_module,
                text_key=input_text_key
            )
            dump_jsonls2jsonl(
                input_path=os.path.join(output_path, '.cleaned'),
                output_path=os.path.join(output_path, 'out'),
                keep_text_only=True,
                source_tag=output_source_value
            )
            log_text(f"Final data dir: {os.path.join(output_path, 'out')}")

    if settings['if_merge']:
        # todo
        pass

    if settings['if_cut']:
        # todo
        pass