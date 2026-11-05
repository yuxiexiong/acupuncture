"""Lazy Qwen3-VL backend. Real loading is gated; unit tests inject a fake backend.

Input rendering/generation contract is adapted from v5 runner.py. No architecture
layer list is assumed: named_modules/named_parameters are inspected at runtime.
"""
import contextlib
import json
import math
import time
from importlib.metadata import version

from common import HERE, REVISION, digest, packed, file_hash, require_live, legacy


def select_tensor(value, path):
    for key in path:
        value = value[key]
    if not hasattr(value, 'shape'):
        raise ValueError('Selected hook value is not a tensor')
    return value


class VLMBackend:
    def __init__(self, config, source, evidence):
        require_live(config)
        self.cfg, self.source, self.evidence = config, source, evidence
        self.model = None
        self.poisoned = False

    def initialize(self):
        if self.poisoned:
            raise RuntimeError('Backend failed initialization/rollback; discard process')
        if self.model is not None:
            return
        try:
            self._initialize()
        except Exception:
            self.poisoned = True
            raise

    def _initialize(self):
        from pathlib import Path
        expected = json.loads((HERE.parent / 'wsp-vlm-channel-prep-v5-2026-11-05/audit/environment_lock.json').read_text())
        if any(version(k) != v for k, v in expected['packages'].items()):
            raise RuntimeError('Frozen v5 environment mismatch')
        for name, h in self.cfg['model_file_sha256'].items():
            if file_hash(Path(self.cfg['model_root']) / name) != h:
                raise ValueError('Fixed model/processor file changed')
        if not set(self.source.file_hashes).issubset(self.cfg['model_file_sha256']):
            raise ValueError('Incomplete checkpoint hash manifest')
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration, GenerationConfig
        if torch.__version__ != '2.6.0+cu124' or not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError('Expected frozen BF16 CUDA environment')
        self.torch = torch
        torch.manual_seed(20261105)
        self.processor = AutoProcessor.from_pretrained(self.cfg['model_root'], local_files_only=True,
                                                      min_pixels=65536, max_pixels=1048576)
        if digest(self.processor.to_json_string().encode()) != self.cfg['processor_sha256']:
            raise ValueError('Processor differs from reviewed previews')
        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            self.cfg['model_root'], local_files_only=True, dtype=torch.bfloat16,
            attn_implementation='sdpa').to('cuda:0').eval()
        self.parameters = dict(self.model.named_parameters(remove_duplicate=False))
        tied = {}
        for name, p in self.parameters.items():
            tied.setdefault((p.data_ptr(), tuple(p.shape), tuple(p.stride())), []).append(name)
        for names in tied.values():
            canonicals = {self.source.canonical(n) for n in names}
            if len(canonicals) != 1:
                raise ValueError('Observed tied parameters differ from frozen alias map: ' + repr(names))
        # Parameter names/dtypes are runtime evidence, never a preselected layer list.
        for name, p in self.parameters.items():
            if list(p.shape) != self.source.entries[self.source.canonical(name)]['shape']:
                raise ValueError('Checkpoint/runtime parameter shape mismatch')
        self.modules = dict(self.model.named_modules())
        self.eos = self.model.generation_config.eos_token_id
        self.generation = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=128,
            eos_token_id=self.eos, pad_token_id=self.processor.tokenizer.pad_token_id, use_cache=True)
        self.screen = legacy('wsp-vlm-channel-prep-v5-2026-11-05/runner.py', 'repair_v5_runner')

    def catalog(self):
        self.initialize()
        return dict(parameters={n: dict(shape=list(p.shape), dtype=str(p.dtype)) for n,p in self.parameters.items()},
                    modules={n: type(m).__name__ for n,m in self.modules.items()})

    def encode(self, request, suffix=''):
        self.initialize()
        from PIL import Image
        # Metadata and gold never enter messages(). Images are selected by frozen ID.
        text = self.processor.apply_chat_template(self.screen.messages(request), tokenize=False, add_generation_prompt=True)
        im = None
        if request['image']:
            path = self.evidence.image(request['request_id'], 'input')
            with Image.open(path) as src:
                im = src.convert('RGB')
        def process(value):
            return self.processor(text=[value], images=[im] if im is not None else None, return_tensors='pt')
        prompt = process(text)
        data = process(text + suffix) if suffix else prompt
        length = prompt['input_ids'].shape[-1]
        if suffix and not self.torch.equal(data['input_ids'][:, :length], prompt['input_ids']):
            raise ValueError('Teacher-forced continuation changes prompt tokenization')
        if data['input_ids'].shape[-1] > self.cfg['contract']['max_input_tokens']:
            raise ValueError('Input token cap exceeded before forward')
        grids = data['image_grid_thw'].tolist() if 'image_grid_thw' in data else []
        ip = self.processor.image_processor
        if dict(ip.size) != {'shortest_edge':65536, 'longest_edge':1048576} or ip.patch_size != 16 or ip.merge_size != 2:
            raise ValueError('Processor geometry changed')
        if bool(grids) != (im is not None):
            raise ValueError('Image/no-image mismatch')
        dims = [[g[1]*16, g[2]*16] for g in grids]
        if any(not 65536 <= h*w <= 1048576 for h,w in dims):
            raise ValueError('Image size outside fixed contract')
        ids = data['input_ids'][0].tolist()
        visual = [i for i,t in enumerate(ids) if t == self.model.config.image_token_id]
        if len(visual) != sum(math.prod(g)//4 for g in grids):
            raise ValueError('Visual token alignment mismatch')
        metadata = dict(input_tokens=len(ids), prompt_tokens=length, image_grid_thw=grids, processed_hw=dims,
                        visual_tokens=len(visual), visual_positions=visual, token_ids=ids,
                        input_ids_sha256=digest(packed(ids)), rendered_chat_sha256=digest((text+suffix).encode()))
        return data.to('cuda:0'), metadata

    @contextlib.contextmanager
    def candidate(self, candidates, candidate):
        self.initialize()
        if self.poisoned:
            raise RuntimeError('Backend rollback failed; discard process')
        active = getattr(self, '_active_candidate', None)
        if active is not None:
            if active != candidate:
                raise ValueError('Cannot nest different candidates')
            yield
            return
        m = candidates.manifest(candidate)
        touched = []
        try:
            with self.torch.no_grad():
                for name in m['tensors']:
                    if name not in self.parameters:
                        raise ValueError('Not a writable runtime parameter: ' + name)
                    p = self.parameters[name]
                    original = self.torch.as_tensor(self.source.load(name), device=p.device, dtype=p.dtype)
                    if not self.torch.equal(p, original):
                        raise ValueError('Runtime not at W0 before candidate')
                    touched.append(name)
                    p.copy_(self.torch.as_tensor(candidates.load(candidate, name), device=p.device, dtype=p.dtype))
            self._active_candidate = candidate
            yield
        finally:
            self._active_candidate = None
            try:
                with self.torch.no_grad():
                    for name in touched:
                        p = self.parameters[name]
                        original = self.torch.as_tensor(self.source.load(name), device=p.device, dtype=p.dtype)
                        p.copy_(original)
                        if not self.torch.equal(p, original):
                            raise RuntimeError('Rollback equality failed')
            except Exception:
                self.poisoned = True
                raise

    def generate(self, request, candidates, candidate, remaining):
        started = time.monotonic()
        inputs, meta = self.encode(request)
        with self.candidate(candidates, candidate), self.torch.inference_mode():
            output = self.model.generate(**inputs, generation_config=self.generation,
                max_time=max(.01, remaining - (time.monotonic()-started)))
        self.torch.cuda.synchronize()
        ids = output[0, meta['input_tokens']:].tolist()
        stop = self.screen.check_generation(ids, self.eos)
        return dict(text=self.processor.decode(ids, skip_special_tokens=True), **stop, **meta,
                    output_tokens=len(ids), generated_ids=ids, status='ok', request_id=request['request_id'])

    def generate_batch(self, requests, candidates, candidate, remaining):
        """Left-pad frozen per-request encodings; images remain in request order."""
        started = time.monotonic()
        encoded = [self.encode(r) for r in requests]
        width = max(meta['input_tokens'] for _,meta in encoded)
        keys = set().union(*(set(data) for data,_ in encoded))
        inputs = {}
        for key in keys:
            if key in ('input_ids','attention_mask','mm_token_type_ids','token_type_ids'):
                example = next(data[key] for data,_ in encoded if key in data)
                fill = self.processor.tokenizer.pad_token_id if key=='input_ids' else 0
                value = self.torch.full((len(requests),width),fill,dtype=example.dtype,device=example.device)
                for i,(data,meta) in enumerate(encoded):
                    if key in data:value[i,-meta['input_tokens']:] = data[key][0]
                inputs[key]=value
            elif key in ('pixel_values','image_grid_thw'):
                inputs[key]=self.torch.cat([data[key] for data,_ in encoded if key in data],dim=0)
            else:
                raise ValueError('Unvalidated batched processor field: '+key)
        with self.candidate(candidates,candidate), self.torch.inference_mode():
            generated=self.model.generate(**inputs,generation_config=self.generation,
                max_time=max(.01,remaining-(time.monotonic()-started)))
        self.torch.cuda.synchronize()
        eos=set(self.eos if isinstance(self.eos,list) else [self.eos])
        outputs=[]
        for i,(request,(_,meta)) in enumerate(zip(requests,encoded)):
            ids=generated[i,width:].tolist()
            stop=next((j+1 for j,t in enumerate(ids) if t in eos),len(ids));ids=ids[:stop]
            outputs.append(dict(text=self.processor.decode(ids,skip_special_tokens=True),
                **self.screen.check_generation(ids,self.eos),**meta,output_tokens=len(ids),generated_ids=ids,
                status='ok',request_id=request['request_id']))
        return outputs

    def measure(self, request, candidates, candidate, spec):
        """One teacher-forced pass; exact modules/tensor paths/flat coordinates supplied by AI.

        Hook arrays retain actual shape and invocation number. Vision patch axes are
        not falsely labeled as decoder token axes. Generated positions can be measured
        using a recorded answer as continuation, explicitly teacher-forced, not natural CoT.
        """
        inputs, meta = self.encode(request, spec.get('continuation', ''))
        handles, captures = [], []
        used = [0]
        limit = self.cfg['contract']['max_measure_elements']
        def register(item, edit):
            module = self.modules[item['module']]
            where = item.get('where', 'output')
            if where not in ('input', 'kwargs', 'output'):
                raise ValueError('Hook where must be input/kwargs/output')
            def hook_value(value):
                tensor = select_tensor(value, item.get('path', []))
                flat = tensor.reshape(-1)
                indices = item.get('flat_indices')
                if indices is not None and (len(set(indices)) != len(indices) or any(type(i) is not int or not 0 <= i < flat.numel() for i in indices)):
                    raise ValueError('Invalid tensor coordinates')
                count = flat.numel() if indices is None else len(indices)
                used[0] += count
                if used[0] > limit:
                    raise ValueError('Diagnostic element budget exceeded')
                if edit:
                    if indices is None:
                        raise ValueError('Temporary intervention needs explicit coordinates')
                    values = self.torch.as_tensor(item['values'], device=tensor.device, dtype=tensor.dtype)
                    if list(values.shape) != [count] or not self.torch.isfinite(values).all():
                        raise ValueError('Invalid intervention values')
                    modified = tensor.clone().contiguous()
                    view = modified.view(-1)
                    op = item['operation']
                    if op == 'add': view[indices] += values
                    elif op == 'replace': view[indices] = values
                    elif op == 'scale': view[indices] *= values
                    else: raise ValueError('Unknown intervention; prepare arbitrary replacement values in Python')
                    if not self.torch.isfinite(modified).all():
                        raise ValueError('Temporary intervention overflow')
                    # Copy preserves tuple/dict output identity and non-contiguous originals.
                    tensor.copy_(modified)
                else:
                    selected = flat if indices is None else flat[indices]
                    captures.append(dict(module=item['module'], where=where, path=item.get('path', []),
                        shape=list(tensor.shape), flat_indices=indices, invocation=len(captures),
                        values=selected.detach().float().cpu().tolist()))
            if where == 'input':
                handles.append(module.register_forward_pre_hook(lambda m, args: hook_value(args)))
            elif where == 'kwargs':
                handles.append(module.register_forward_pre_hook(lambda m, args, kwargs: hook_value(kwargs), with_kwargs=True))
            else:
                handles.append(module.register_forward_hook(lambda m, args, out: hook_value(out)))
        try:
            for item in spec.get('interventions', []): register(item, True)
            for item in spec.get('capture', []): register(item, False)
            with self.candidate(candidates, candidate), self.torch.inference_mode():
                output = self.model(**inputs, use_cache=False, return_dict=True)
            start = meta['prompt_tokens']
            scores = []
            for i in range(start, meta['input_tokens']):
                lp = self.torch.log_softmax(output.logits[0, i-1].float(), dim=-1)
                scores.append(float(lp[meta['token_ids'][i]]))
            next_logits = output.logits[0, -1].float()
            token_ids = spec.get('score_token_ids', [])
            if any(type(i) is not int or not 0 <= i < next_logits.numel() for i in token_ids):
                raise ValueError('Invalid score token IDs')
            return dict(kind='temporary_intervention' if spec.get('interventions') else 'measurement',
                        candidate=candidate, captures=captures, **meta, output_tokens=0,
                        continuation_logprobs=scores,
                        next_token_logits={str(i):float(next_logits[i]) for i in token_ids})
        finally:
            for handle in handles:
                handle.remove()
