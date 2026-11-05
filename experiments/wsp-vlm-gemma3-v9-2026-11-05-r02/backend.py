"""Gemma 3 adapter; reuse Qwen's observation, editing, batching and measurement.

Input rendering/generation contract is adapted from v5 runner.py. No architecture
layer list is assumed: named_modules/named_parameters are inspected at runtime.
"""
import contextlib
import json
import math
import time
from importlib.metadata import version

from common import HERE, REVISION, digest, packed, file_hash, require_live, legacy


def runtime_name(name):
    """Official checkpoint names predate Transformers' multimodal prefix layout."""
    for old,new in (('language_model.model.','model.language_model.'),
                    ('language_model.lm_head.','lm_head.'),
                    ('vision_tower.vision_model.','model.vision_tower.'),
                    ('multi_modal_projector.','model.multi_modal_projector.')):
        if name.startswith(old):return new+name[len(old):]
    raise ValueError('Unexpected Gemma checkpoint parameter: '+name)


def checkpoint_aliases(names):
    aliases={runtime_name(n):n for n in names if runtime_name(n)!=n}
    if 'language_model.lm_head.weight' not in names:
        aliases['lm_head.weight']='language_model.model.embed_tokens.weight'
    return aliases


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
        from transformers import AutoProcessor, Gemma3ForConditionalGeneration, GenerationConfig
        if torch.__version__ != '2.6.0+cu124' or not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
            raise RuntimeError('Expected frozen BF16 CUDA environment')
        self.torch = torch
        torch.manual_seed(20261105)
        self.processor = AutoProcessor.from_pretrained(self.cfg['model_root'], local_files_only=True)
        if digest(self.processor.to_json_string().encode()) != self.cfg['processor_sha256']:
            raise ValueError('Processor differs from reviewed previews')
        self.model, loading = Gemma3ForConditionalGeneration.from_pretrained(
            self.cfg['model_root'], local_files_only=True, dtype=torch.bfloat16,
            attn_implementation='sdpa', output_loading_info=True)
        if any(loading.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')):
            raise ValueError('Checkpoint/runtime loading mismatch: '+repr(loading))
        self.model=self.model.to('cuda:0').eval()
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
        # Candidate manifests keep the original checkpoint names and tensor bytes.
        for name,p in list(self.parameters.items()):
            self.parameters.setdefault(self.source.canonical(name),p)
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
            # The native chat template already includes BOS. Never add a second BOS.
            return self.processor(text=[value], images=[im] if im is not None else None,
                                  return_tensors='pt',add_special_tokens=False,do_pan_and_scan=False)
        prompt = process(text)
        data = process(text + suffix) if suffix else prompt
        length = prompt['input_ids'].shape[-1]
        if suffix and not self.torch.equal(data['input_ids'][:, :length], prompt['input_ids']):
            raise ValueError('Teacher-forced continuation changes prompt tokenization')
        if data['input_ids'].shape[-1] > self.cfg['contract']['max_input_tokens']:
            raise ValueError('Input token cap exceeded before forward')
        ip = self.processor.image_processor
        if dict(ip.size) != {'height':896, 'width':896} or self.processor.image_seq_length != 256:
            raise ValueError('Processor geometry changed')
        pixels=data.get('pixel_values')
        if (pixels is not None) != (im is not None):
            raise ValueError('Image/no-image mismatch')
        if pixels is not None and list(pixels.shape) != [1,3,896,896]:
            raise ValueError('Unexpected crop count or Gemma image shape')
        dims = [[896,896]] if pixels is not None else []
        ids = data['input_ids'][0].tolist()
        visual = [i for i,t in enumerate(ids) if t == self.model.config.image_token_id]
        if len(visual) != (256 if im is not None else 0):
            raise ValueError('Visual token alignment mismatch')
        if ids[0] != self.processor.tokenizer.bos_token_id or ids.count(self.processor.tokenizer.bos_token_id)!=1:
            raise ValueError('Native template must have exactly one BOS')
        if 'token_type_ids' not in data:
            raise ValueError('Gemma image/text attention types missing')
        types=data['token_type_ids'][0].tolist()
        if [i for i,t in enumerate(types) if t==1] != visual:
            raise ValueError('Gemma image bidirectional attention types misaligned')
        metadata = dict(input_tokens=len(ids), prompt_tokens=length, image_grid_thw=[], processed_hw=dims,
                        visual_tokens=len(visual), visual_positions=visual, token_ids=ids,
                        token_type_ids_sha256=digest(packed(types)),
                        input_ids_sha256=digest(packed(ids)), rendered_chat_sha256=digest((text+suffix).encode()))
        return data.to('cuda:0'), metadata

    def verify_native_inputs(self, request):
        """Compare our assembly to the installed processor's official chat entry."""
        adapted,_=self.encode(request)
        original=dict(request)
        if request['image']:original['image']=str(self.evidence.image(request['request_id'],'input'))
        native=self.processor.apply_chat_template(self.screen.messages(original), tokenize=True,
            add_generation_prompt=True, return_dict=True,return_tensors='pt',do_pan_and_scan=False)
        if set(native)!=set(adapted):raise ValueError('Native processor fields differ')
        for key in native:
            if not self.torch.equal(native[key].cpu(),adapted[key].cpu()):
                raise ValueError('Native Gemma inputs differ: '+key)
        return dict(request_id=request['request_id'],fields=list(native),equal=True)

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
        spec = dict(spec)
        captures_requested = list(spec.get('capture', []))
        for layer in spec.get('layers', []):
            if type(layer) is not int or layer < 0:
                raise ValueError('Invalid decoder layer')
            name = f'model.language_model.layers.{layer}'
            if name not in self.modules or name+'.mlp.down_proj' not in self.modules:
                raise ValueError('No verified decoder/MLP mapping for requested layer')
            captures_requested.extend([dict(module=name, where='output', token_positions=spec.get('token_positions','last_prompt')),
                dict(module=name+'.mlp.down_proj', where='input', path=[0], token_positions=spec.get('token_positions','last_prompt'))])
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
                positions = item.get('token_positions')
                selected_tensor = tensor
                if positions is not None:
                    if edit or tensor.ndim != 3 or tensor.shape[0] != 1 or tensor.shape[1] != meta['input_tokens']:
                        raise ValueError('Token selector requires [1,input_tokens,width] capture, not vision/temporary edit')
                    positions = [meta['prompt_tokens']-1] if positions == 'last_prompt' else positions
                    if not isinstance(positions,list) or not positions or any(type(i) is not int or not 0<=i<meta['input_tokens'] for i in positions):
                        raise ValueError('Invalid token positions')
                    selected_tensor = tensor[:,positions,:]
                flat = selected_tensor.reshape(-1)
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
                        shape=list(tensor.shape), selected_shape=list(selected_tensor.shape), token_positions=positions, flat_indices=indices, invocation=len(captures),
                        values=selected.detach().float().cpu().tolist()))
            if where == 'input':
                handles.append(module.register_forward_pre_hook(lambda m, args: hook_value(args)))
            elif where == 'kwargs':
                handles.append(module.register_forward_pre_hook(lambda m, args, kwargs: hook_value(kwargs), with_kwargs=True))
            else:
                handles.append(module.register_forward_hook(lambda m, args, out: hook_value(out)))
        try:
            for item in spec.get('interventions', []): register(item, True)
            for item in captures_requested: register(item, False)
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
